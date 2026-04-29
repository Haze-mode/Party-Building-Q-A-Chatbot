import json
import random
from pathlib import Path
from typing import Dict, List, Optional


SYSTEM_PROMPT = (
    "你是一个专业的党建知识助手，负责准确、严肃地回答关于中国共产党党史、章程及政策的问题。"
)


def read_jsonl(path: Path) -> List[Dict]:
    rows: List[Dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: List[Dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_sample(
    user_text: str,
    assistant_text: str,
    source_title: str,
    source_section: str,
    source_year: Optional[int] = None,
    source_url: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Dict:
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": assistant_text},
        ],
        "traceability": {
            "source_title": source_title,
            "source_section": source_section,
            "source_year": source_year,
            "source_url": source_url,
            "tags": tags or ["党建", "政策理论"],
        },
    }


def normalize_item(item: Dict) -> Optional[Dict]:
    msgs = item.get("messages", [])
    if len(msgs) != 3:
        return None
    if msgs[0].get("role") != "system" or msgs[1].get("role") != "user" or msgs[2].get("role") != "assistant":
        return None

    msgs[0]["content"] = SYSTEM_PROMPT
    msgs[2]["content"] = msgs[2]["content"].replace("极极少数", "极少数")

    trace = item.get("traceability")
    if not isinstance(trace, dict):
        item["traceability"] = {
            "source_title": "历史党建知识集（待补充精确出处）",
            "source_section": "基础问答",
            "source_year": None,
            "source_url": None,
            "tags": ["党建", "基础知识"],
        }
    return item


def build_latest_traceable_samples() -> List[Dict]:
    return [
        build_sample(
            "党的二十大报告对新时代新征程中国共产党的中心任务是怎么表述的？",
            "党的二十大报告指出：新时代新征程中国共产党的中心任务是团结带领全国各族人民全面建成社会主义现代化强国、实现第二个百年奋斗目标，以中国式现代化全面推进中华民族伟大复兴。",
            source_title="中国共产党第二十次全国代表大会报告",
            source_section="大会主题与中心任务",
            source_year=2022,
            source_url="https://www.gov.cn/xinwen/2022-10/25/content_5721685.htm",
            tags=["二十大", "中国式现代化"],
        ),
        build_sample(
            "什么是中国式现代化的本质要求？",
            "中国式现代化强调坚持中国共产党领导，坚持中国特色社会主义，实现高质量发展，发展全过程人民民主，丰富人民精神世界，实现全体人民共同富裕，促进人与自然和谐共生，推动构建人类命运共同体，创造人类文明新形态。",
            source_title="中国共产党第二十次全国代表大会报告",
            source_section="中国式现代化",
            source_year=2022,
            source_url="https://www.gov.cn/xinwen/2022-10/25/content_5721685.htm",
            tags=["二十大", "中国式现代化"],
        ),
        build_sample(
            "如何理解“高质量发展是全面建设社会主义现代化国家的首要任务”？",
            "这句话强调发展质量和效益优先。要完整、准确、全面贯彻新发展理念，加快构建新发展格局，推动经济实现质的有效提升和量的合理增长，为现代化建设提供坚实物质技术基础。",
            source_title="中国共产党第二十次全国代表大会报告",
            source_section="高质量发展",
            source_year=2022,
            source_url="https://www.gov.cn/xinwen/2022-10/25/content_5721685.htm",
            tags=["高质量发展"],
        ),
        build_sample(
            "新质生产力通常如何理解？",
            "新质生产力通常指以科技创新为主导、摆脱传统高消耗增长路径、符合高质量发展要求的先进生产力形态。其关键在于技术革命性突破、生产要素创新性配置和产业深度转型升级。",
            source_title="中央经济工作会议与相关重要论述",
            source_section="发展新质生产力",
            source_year=2023,
            source_url="https://www.gov.cn/yaowen/liebiao/202312/content_6920376.htm",
            tags=["新质生产力", "科技创新"],
        ),
        build_sample(
            "发展新质生产力和党建工作有什么关系？",
            "党建工作可以通过强化政治引领、组织保障和人才支撑，为科技创新和产业升级营造良好环境。坚持党的领导，有助于把创新资源更好组织起来，服务高质量发展。",
            source_title="关于高质量发展和党的领导的重要论述",
            source_section="党建引领高质量发展",
            source_year=2023,
            source_url=None,
            tags=["新质生产力", "党建引领"],
        ),
        build_sample(
            "党纪学习教育的重点一般包括哪些方面？",
            "重点通常包括学纪、知纪、明纪、守纪，把纪律建设摆在更加突出位置，推动党员干部把遵规守纪刻印在心，形成干事创业、清正廉洁的良好氛围。",
            source_title="关于在全党开展党纪学习教育的通知",
            source_section="总体要求",
            source_year=2024,
            source_url=None,
            tags=["党纪学习教育", "全面从严治党"],
        ),
        build_sample(
            "中央八项规定精神为什么要常态化落实？",
            "常态化落实有助于持续纠治“四风”，防止问题反弹回潮，推动作风建设常抓不懈、久久为功，进一步密切党同人民群众的血肉联系。",
            source_title="中共中央八项规定及其实施细则精神",
            source_section="作风建设常态化长效化",
            source_year=2012,
            source_url="https://www.gov.cn/jrzg/2012-12/04/content_2288203.htm",
            tags=["八项规定", "作风建设"],
        ),
        build_sample(
            "什么是全过程人民民主？",
            "全过程人民民主是社会主义民主政治的本质属性，强调民主选举、民主协商、民主决策、民主管理、民主监督各环节贯通，保障人民当家作主具体、现实地体现在国家政治生活和社会生活中。",
            source_title="党的二十大报告与相关制度文件",
            source_section="发展全过程人民民主",
            source_year=2022,
            source_url="https://www.gov.cn/xinwen/2022-10/25/content_5721685.htm",
            tags=["全过程人民民主"],
        ),
        build_sample(
            "什么是党的自我革命？",
            "党的自我革命是党始终保持先进性和纯洁性的根本途径，核心是坚持真理、修正错误，刀刃向内、刮骨疗毒，不断提高自我净化、自我完善、自我革新、自我提高能力。",
            source_title="二十届中央纪委历次全会公报及相关重要论述",
            source_section="党的自我革命",
            source_year=2024,
            source_url=None,
            tags=["自我革命", "全面从严治党"],
        ),
    ]


def make_rewrites(seed_items: List[Dict], max_count: int = 20) -> List[Dict]:
    templates = [
        "请问{}",
        "{}？请简要说明。",
        "能解释一下{}吗？",
        "关于{}，标准表述是什么？",
    ]
    out: List[Dict] = []
    for i, item in enumerate(seed_items[:max_count]):
        q = item["messages"][1]["content"].rstrip("？?")
        a = item["messages"][2]["content"]
        trace = item.get("traceability", {})
        out.append(
            build_sample(
                user_text=templates[i % len(templates)].format(q),
                assistant_text=a,
                source_title=trace.get("source_title", "历史党建知识集（待补充精确出处）"),
                source_section=trace.get("source_section", "问法改写增强"),
                source_year=trace.get("source_year"),
                source_url=trace.get("source_url"),
                tags=list(set((trace.get("tags") or []) + ["问法增强"])),
            )
        )
    return out


def main() -> None:
    data_dir = Path(__file__).parent
    train_path = data_dir / "train.jsonl"
    dev_path = data_dir / "dev.jsonl"
    test_path = data_dir / "test.jsonl"

    merged: List[Dict] = []
    for path in (train_path, dev_path, test_path):
        merged.extend(read_jsonl(path))

    normalized: List[Dict] = []
    for item in merged:
        row = normalize_item(item)
        if row is not None:
            normalized.append(row)

    # 按问句去重
    deduped: List[Dict] = []
    seen_q = set()
    for item in normalized:
        q = item["messages"][1]["content"].strip()
        if q in seen_q:
            continue
        seen_q.add(q)
        deduped.append(item)

    latest_samples = build_latest_traceable_samples()
    rewrites = make_rewrites(deduped, max_count=24)
    all_items = deduped + latest_samples + rewrites

    # 按问答对去重，防止增强重复
    unique_items: List[Dict] = []
    seen_pair = set()
    for item in all_items:
        q = item["messages"][1]["content"].strip()
        a = item["messages"][2]["content"].strip()
        k = (q, a)
        if k in seen_pair:
            continue
        seen_pair.add(k)
        unique_items.append(item)

    rng = random.Random(20260426)
    rng.shuffle(unique_items)

    n = len(unique_items)
    n_train = int(0.8 * n)
    n_dev = int(0.1 * n)
    n_test = n - n_train - n_dev

    train_rows = unique_items[:n_train]
    dev_rows = unique_items[n_train:n_train + n_dev]
    test_rows = unique_items[n_train + n_dev:]

    # 保留原训练格式（仅 messages）
    write_jsonl(train_path, [{"messages": x["messages"]} for x in train_rows])
    write_jsonl(dev_path, [{"messages": x["messages"]} for x in dev_rows])
    write_jsonl(test_path, [{"messages": x["messages"]} for x in test_rows])

    # 新增可追溯版本
    write_jsonl(data_dir / "train_traceable.jsonl", train_rows)
    write_jsonl(data_dir / "dev_traceable.jsonl", dev_rows)
    write_jsonl(data_dir / "test_traceable.jsonl", test_rows)
    write_jsonl(data_dir / "traceable_full.jsonl", unique_items)

    print(
        f"total={n}, train={len(train_rows)}, dev={len(dev_rows)}, test={len(test_rows)}"
    )
    print("wrote: train/dev/test + *_traceable + traceable_full")


if __name__ == "__main__":
    main()
