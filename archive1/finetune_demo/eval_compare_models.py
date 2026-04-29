import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple, Union

import torch
from peft import AutoPeftModelForCausalLM, PeftModelForCausalLM
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    PreTrainedModel,
    PreTrainedTokenizer,
    PreTrainedTokenizerFast,
)

ModelType = Union[PreTrainedModel, PeftModelForCausalLM]
TokenizerType = Union[PreTrainedTokenizer, PreTrainedTokenizerFast]


def read_jsonl(path: Path) -> List[Dict]:
    rows: List[Dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def tokenize_zh_chars(text: str) -> List[str]:
    # 字符级分词，避免依赖 jieba 等第三方库
    return [ch for ch in text.strip() if not ch.isspace()]


def ngrams(tokens: List[str], n: int) -> List[Tuple[str, ...]]:
    if len(tokens) < n:
        return []
    return [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def rouge_n_f1(pred: str, ref: str, n: int) -> float:
    p_tokens = tokenize_zh_chars(pred)
    r_tokens = tokenize_zh_chars(ref)
    p_ngrams = Counter(ngrams(p_tokens, n))
    r_ngrams = Counter(ngrams(r_tokens, n))
    overlap = 0
    for ng, c in p_ngrams.items():
        overlap += min(c, r_ngrams.get(ng, 0))
    if overlap == 0:
        return 0.0
    precision = overlap / max(sum(p_ngrams.values()), 1)
    recall = overlap / max(sum(r_ngrams.values()), 1)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def lcs_len(a: List[str], b: List[str]) -> int:
    m, n = len(a), len(b)
    dp = [0] * (n + 1)
    for i in range(1, m + 1):
        prev = 0
        for j in range(1, n + 1):
            tmp = dp[j]
            if a[i - 1] == b[j - 1]:
                dp[j] = prev + 1
            else:
                dp[j] = max(dp[j], dp[j - 1])
            prev = tmp
    return dp[n]


def rouge_l_f1(pred: str, ref: str) -> float:
    p = tokenize_zh_chars(pred)
    r = tokenize_zh_chars(ref)
    if not p or not r:
        return 0.0
    ll = lcs_len(p, r)
    precision = ll / len(p)
    recall = ll / len(r)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def bleu4(pred: str, ref: str) -> float:
    p = tokenize_zh_chars(pred)
    r = tokenize_zh_chars(ref)
    if not p or not r:
        return 0.0

    log_precisions = []
    for n in range(1, 5):
        p_ng = Counter(ngrams(p, n))
        r_ng = Counter(ngrams(r, n))
        total = max(sum(p_ng.values()), 1)
        match = 0
        for ng, cnt in p_ng.items():
            match += min(cnt, r_ng.get(ng, 0))
        # 平滑，避免 0
        prec = (match + 1) / (total + 1)
        log_precisions.append(math.log(prec))
    geo_mean = math.exp(sum(log_precisions) / 4.0)

    # brevity penalty
    if len(p) > len(r):
        bp = 1.0
    else:
        bp = math.exp(1 - len(r) / max(len(p), 1))
    return bp * geo_mean


def load_model_and_tokenizer(model_dir: Union[str, Path], trust_remote_code: bool = True) -> Tuple[ModelType, TokenizerType]:
    model_dir = Path(model_dir).expanduser().resolve()
    if (model_dir / "adapter_config.json").exists():
        model = AutoPeftModelForCausalLM.from_pretrained(
            model_dir,
            trust_remote_code=trust_remote_code,
            device_map="auto",
        )
        tokenizer_dir = model.peft_config["default"].base_model_name_or_path
    else:
        model = AutoModelForCausalLM.from_pretrained(
            model_dir,
            trust_remote_code=trust_remote_code,
            device_map="auto",
        )
        tokenizer_dir = model_dir

    tokenizer = AutoTokenizer.from_pretrained(
        tokenizer_dir,
        trust_remote_code=trust_remote_code,
        encode_special_tokens=True,
        use_fast=False,
    )
    model.eval()
    return model, tokenizer


@torch.no_grad()
def generate_answer(
    model: ModelType,
    tokenizer: TokenizerType,
    system_prompt: str,
    user_prompt: str,
    max_new_tokens: int,
) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    inputs = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=True,
        return_tensors="pt",
    ).to(model.device)

    outputs = model.generate(
        input_ids=inputs,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        temperature=1.0,
        top_p=1.0,
        repetition_penalty=1.1,
        eos_token_id=model.config.eos_token_id,
    )
    gen_tokens = outputs[0][inputs.shape[-1]:]
    text = tokenizer.decode(gen_tokens, skip_special_tokens=True)
    return text.strip()


def score_pair(pred: str, ref: str) -> Dict[str, float]:
    return {
        "rouge1_f1": rouge_n_f1(pred, ref, 1),
        "rouge2_f1": rouge_n_f1(pred, ref, 2),
        "rougeL_f1": rouge_l_f1(pred, ref),
        "bleu4": bleu4(pred, ref),
    }


def mean_scores(items: List[Dict[str, float]]) -> Dict[str, float]:
    if not items:
        return {"rouge1_f1": 0.0, "rouge2_f1": 0.0, "rougeL_f1": 0.0, "bleu4": 0.0}
    keys = items[0].keys()
    return {k: sum(x[k] for x in items) / len(items) for k in keys}


def evaluate_model(
    model: ModelType,
    tokenizer: TokenizerType,
    samples: List[Dict],
    max_new_tokens: int,
    limit: int,
) -> Tuple[Dict[str, float], List[Dict]]:
    subset = samples[:limit] if limit > 0 else samples
    all_scores: List[Dict[str, float]] = []
    details: List[Dict] = []

    for idx, row in enumerate(subset):
        msgs = row["messages"]
        system_prompt = msgs[0]["content"]
        user_prompt = msgs[1]["content"]
        ref_answer = msgs[2]["content"]
        pred = generate_answer(
            model=model,
            tokenizer=tokenizer,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_new_tokens=max_new_tokens,
        )
        score = score_pair(pred, ref_answer)
        all_scores.append(score)
        details.append(
            {
                "index": idx,
                "user": user_prompt,
                "reference": ref_answer,
                "prediction": pred,
                "metrics": score,
            }
        )
        print(f"[{idx + 1}/{len(subset)}] done")
    return mean_scores(all_scores), details


def main() -> None:
    parser = argparse.ArgumentParser(description="比较微调前后模型在党建问答集上的ROUGE/BLEU")
    parser.add_argument("--base_model", required=True, help="微调前模型路径")
    parser.add_argument("--finetuned_model", required=True, help="微调后模型或LoRA路径")
    parser.add_argument("--eval_file", default="data/test.jsonl", help="评测集路径")
    parser.add_argument("--output_file", default="eval_compare_report.json", help="输出报告JSON")
    parser.add_argument("--max_new_tokens", type=int, default=256, help="生成长度")
    parser.add_argument("--limit", type=int, default=0, help="仅评测前N条，0表示全量")
    args = parser.parse_args()

    eval_path = Path(args.eval_file).expanduser().resolve()
    output_path = Path(args.output_file).expanduser().resolve()
    samples = read_jsonl(eval_path)
    if not samples:
        raise ValueError(f"评测集为空: {eval_path}")

    print("loading base model...")
    base_model, base_tok = load_model_and_tokenizer(args.base_model)
    print("evaluating base model...")
    base_avg, base_details = evaluate_model(
        model=base_model,
        tokenizer=base_tok,
        samples=samples,
        max_new_tokens=args.max_new_tokens,
        limit=args.limit,
    )

    print("loading finetuned model...")
    ft_model, ft_tok = load_model_and_tokenizer(args.finetuned_model)
    print("evaluating finetuned model...")
    ft_avg, ft_details = evaluate_model(
        model=ft_model,
        tokenizer=ft_tok,
        samples=samples,
        max_new_tokens=args.max_new_tokens,
        limit=args.limit,
    )

    diff = {k: ft_avg[k] - base_avg[k] for k in ft_avg.keys()}
    report = {
        "eval_file": str(eval_path),
        "sample_count": len(base_details),
        "base_model": str(Path(args.base_model).expanduser()),
        "finetuned_model": str(Path(args.finetuned_model).expanduser()),
        "average_metrics": {
            "base": base_avg,
            "finetuned": ft_avg,
            "diff_finetuned_minus_base": diff,
        },
        "details": {
            "base": base_details,
            "finetuned": ft_details,
        },
    }

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(json.dumps(report["average_metrics"], ensure_ascii=False, indent=2))
    print(f"report saved: {output_path}")


if __name__ == "__main__":
    main()
