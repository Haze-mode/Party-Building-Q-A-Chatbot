"""
This script creates a CLI demo with transformers backend for the glm-4-9b model,
allowing users to interact with the model through a command-line interface.

Usage:
- Run the script to start the CLI demo.
- Interact with the model by typing questions and receiving responses.

Note: The script includes a modification to handle markdown to plain text conversion,
ensuring that the CLI interface displays formatted text correctly.
"""
import os
import torch
from threading import Thread
from typing import Union
from pathlib import Path
import numpy as np
from peft import AutoPeftModelForCausalLM, PeftModelForCausalLM
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter  # ✅ 正确的写法
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    PreTrainedModel,
    PreTrainedTokenizer,
    PreTrainedTokenizerFast,
    StoppingCriteria,
    StoppingCriteriaList,
    TextIteratorStreamer
)

ModelType = Union[PreTrainedModel, PeftModelForCausalLM]
TokenizerType = Union[PreTrainedTokenizer, PreTrainedTokenizerFast]

# MODEL_PATH = os.environ.get('MODEL_PATH', '/root/GLM-4/finetune_demo/output/模型保存点')
# MODEL_PATH = os.environ.get('MODEL_PATH', '/root/GLM-4/finetune_demo/output/checkpoint-2950')
MODEL_PATH = os.environ.get('MODEL_PATH', '/root/autodl-tmp/glm-4-9b-chat/')

def load_knowledge_base(directory):
    """从目录加载文档并切分成段落"""

    documents = []
    for file in os.listdir(directory):
        path = os.path.join(directory, file)
        if file.endswith(".txt"):
            loader = TextLoader(path, encoding="utf-8")
        elif file.endswith(".pdf"):
            loader = PyPDFLoader(path)
        elif file.endswith(".docx"):
            loader = Docx2txtLoader(path)
        else:
            continue
        documents.extend(loader.load())
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    splits = splitter.split_documents(documents)
    return [doc.page_content for doc in splits]

def retrieve(query, vectorizer, tfidf, paragraphs, k=3):
    import numpy as np
    q_vec = vectorizer.transform([query])
    scores = np.dot(tfidf, q_vec.T).toarray().flatten()
    top_idx = scores.argsort()[-k:][::-1]
    return [paragraphs[i] for i in top_idx]
def build_tfidf_index(knowledge_base):
    from sklearn.feature_extraction.text import TfidfVectorizer
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(knowledge_base)
    return vectorizer, tfidf_matrix

def load_model_and_tokenizer(
        model_dir: Union[str, Path], trust_remote_code: bool = True
) -> tuple[ModelType, TokenizerType]:
    model_dir = Path(model_dir).expanduser().resolve()
    if (model_dir / 'adapter_config.json').exists():
        model = AutoPeftModelForCausalLM.from_pretrained(
            model_dir, trust_remote_code=trust_remote_code, device_map='auto')
        tokenizer_dir = model.peft_config['default'].base_model_name_or_path
    else:
        model = AutoModelForCausalLM.from_pretrained(model_dir, trust_remote_code=trust_remote_code, device_map='auto')
        tokenizer_dir = model_dir

    tokenizer = AutoTokenizer.from_pretrained(
        tokenizer_dir, trust_remote_code=trust_remote_code, encode_special_tokens=True, use_fast=False
    )
    return model, tokenizer


model, tokenizer = load_model_and_tokenizer(MODEL_PATH, trust_remote_code=True)


class StopOnTokens(StoppingCriteria):
    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        stop_ids = model.config.eos_token_id
        for stop_id in stop_ids:
            if input_ids[0][-1] == stop_id:
                return True
        return False


if __name__ == "__main__":
    # 加载知识库（请修改为你的知识库目录）
    KB_DIR = "党建知识库"  # 存放党建文档的文件夹
    paragraphs = load_knowledge_base(KB_DIR)
    vectorizer, tfidf = build_tfidf_index(paragraphs)

    history = []
    max_length = 1024
    top_p = 0.7
    temperature = 0.9
    stop = StopOnTokens()


    print("党建小助手启动了")

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        history.append([user_input, ""])

        # 1. 检索相关知识
        retrieved = retrieve(user_input, vectorizer, tfidf, paragraphs, k=3)
        context = "\n\n".join(retrieved)

        # 2. 构建消息列表
        messages = [
            {"role": "system", "content": f"请基于以下已知信息回答问题：\n{context}"}
        ]
        # messages = []
        for idx, (user_msg, model_msg) in enumerate(history):
            if idx == len(history) - 1 and not model_msg:
                messages.append({"role": "user", "content": user_msg})
                break
            if user_msg:
                messages.append({"role": "user", "content": user_msg})
            if model_msg:
                messages.append({"role": "assistant", "content": model_msg})
        model_inputs = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_tensors="pt"
        ).to(model.device)
        streamer = TextIteratorStreamer(
            tokenizer=tokenizer,
            timeout=60,
            skip_prompt=True,
            skip_special_tokens=True
        )
        generate_kwargs = {
            "input_ids": model_inputs,
            "streamer": streamer,
            "max_new_tokens": max_length,
            "do_sample": True,
            "top_p": top_p,
            "temperature": temperature,
            "stopping_criteria": StoppingCriteriaList([stop]),
            "repetition_penalty": 1.2,
            "eos_token_id": model.config.eos_token_id,
        }
        t = Thread(target=model.generate, kwargs=generate_kwargs)
        t.start()
        print("GLM-4:", end="", flush=True)
        for new_token in streamer:
            if new_token:
                print(new_token, end="", flush=True)
                history[-1][1] += new_token

        history[-1][1] = history[-1][1].strip()
