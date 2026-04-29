import json
import random
from pathlib import Path


SYSTEM_PROMPT = (
    "你是一个专业的党建知识助手，负责准确、严肃地回答关于中国共产党党史、章程及政策的问题。"
)


def read_jsonl(path: Path):
    items = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def write_jsonl(path: Path, items):
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def build_sample(user_text: str, assistant_text: str):
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": assistant_text},
        ]
    }


def normalize_item(item):
    msgs = item.get("messages", [])
    if len(msgs) != 3:
        return None
    if msgs[0].get("role") != "system":
        return None
    if msgs[1].get("role") != "user":
        return None
    if msgs[2].get("role") != "assistant":
        return None

    # 统一 system，避免模型学习到多种等价 system 描述
    msgs[0]["content"] = SYSTEM_PROMPT

    # 已知文本瑕疵修正
    msgs[2]["content"] = msgs[2]["content"].replace("极极少数", "极少数")
    return item


def main():
    data_dir = Path(__file__).parent
    train_path = data_dir / "train.jsonl"
    dev_path = data_dir / "dev.jsonl"
    test_path = data_dir / "test.jsonl"

    merged = []
    for p in (train_path, dev_path, test_path):
        merged.extend(read_jsonl(p))

    cleaned = []
    for item in merged:
        ni = normalize_item(item)
        if ni is not None:
            cleaned.append(ni)

    # 按 user 问题去重，减少跨集合重复
    seen_user = set()
    deduped = []
    for item in cleaned:
        user_q = item["messages"][1]["content"].strip()
        if user_q in seen_user:
            continue
        seen_user.add(user_q)
        deduped.append(item)

    # 近年党建热点样本（知识点尽量稳定、通用）
    latest_samples = [
        build_sample(
            "党的二十大报告对新时代新征程中国共产党的中心任务是怎么表述的？",
            "党的二十大报告指出：新时代新征程中国共产党的中心任务是团结带领全国各族人民全面建成社会主义现代化强国、实现第二个百年奋斗目标，以中国式现代化全面推进中华民族伟大复兴。",
        ),
        build_sample(
            "什么是中国式现代化的本质要求？",
            "中国式现代化强调坚持中国共产党领导，坚持中国特色社会主义，实现高质量发展，发展全过程人民民主，丰富人民精神世界，实现全体人民共同富裕，促进人与自然和谐共生，推动构建人类命运共同体，创造人类文明新形态。",
        ),
        build_sample(
            "如何理解“高质量发展是全面建设社会主义现代化国家的首要任务”？",
            "这句话强调发展质量和效益优先。要完整、准确、全面贯彻新发展理念，加快构建新发展格局，推动经济实现质的有效提升和量的合理增长，为现代化建设提供坚实物质技术基础。",
        ),
        build_sample(
            "新质生产力通常如何理解？",
            "新质生产力通常指以科技创新为主导、摆脱传统高消耗增长路径、符合高质量发展要求的先进生产力形态。其关键在于技术革命性突破、生产要素创新性配置和产业深度转型升级。",
        ),
        build_sample(
            "发展新质生产力和党建工作有什么关系？",
            "党建工作可以通过强化政治引领、组织保障和人才支撑，为科技创新和产业升级营造良好环境。坚持党的领导，有助于把创新资源更好组织起来，服务高质量发展。",
        ),
        build_sample(
            "为什么要把全面从严治党长期坚持下去？",
            "全面从严治党是新时代党的自我革命的战略方针。长期坚持有利于保持党的先进性和纯洁性，提升执政能力和领导水平，为推进中国式现代化提供坚强政治保证。",
        ),
        build_sample(
            "党纪学习教育的重点一般包括哪些方面？",
            "重点通常包括学纪、知纪、明纪、守纪，把纪律建设摆在更加突出位置，推动党员干部把遵规守纪刻印在心，形成干事创业、清正廉洁的良好氛围。",
        ),
        build_sample(
            "中央八项规定精神为什么要常态化落实？",
            "常态化落实有助于持续纠治“四风”，防止问题反弹回潮，推动作风建设常抓不懈、久久为功，进一步密切党同人民群众的血肉联系。",
        ),
        build_sample(
            "如何理解“坚持和加强党的全面领导”？",
            "就是在改革发展稳定、内政外交国防、治党治国治军各领域各方面，始终坚持党中央集中统一领导，确保全党全国在政治立场、政治方向、政治原则、政治道路上同党中央保持高度一致。",
        ),
        build_sample(
            "什么是全过程人民民主？",
            "全过程人民民主是社会主义民主政治的本质属性，强调民主选举、民主协商、民主决策、民主管理、民主监督各环节贯通，保障人民当家作主具体、现实地体现在国家政治生活和社会生活中。",
        ),
        build_sample(
            "基层党组织在乡村振兴中可以发挥哪些作用？",
            "基层党组织可以发挥战斗堡垒作用，统筹产业发展、乡村治理、公共服务和人才培养，组织群众、宣传群众、凝聚群众、服务群众，推动乡村全面振兴。",
        ),
        build_sample(
            "在国有企业中，党建和生产经营如何融合？",
            "关键是把党的领导融入公司治理各环节，把党建工作与改革发展重点任务同谋划、同部署、同推进、同考核，推动党建优势转化为治理效能和发展优势。",
        ),
        build_sample(
            "机关党建如何服务高质量发展？",
            "机关党建应围绕中心、建设队伍、服务群众，通过强化理论武装、改进作风、提高执行力，把党的政治优势和组织优势转化为推动高质量发展的实际成效。",
        ),
        build_sample(
            "什么是党的自我革命？",
            "党的自我革命是党始终保持先进性和纯洁性的根本途径，核心是坚持真理、修正错误，刀刃向内、刮骨疗毒，不断提高自我净化、自我完善、自我革新、自我提高能力。",
        ),
        build_sample(
            "为什么说作风建设永远在路上？",
            "作风问题具有顽固性和反复性，必须经常抓、长期抓。只有持续深化纠治“四风”，才能不断巩固党长期执政的群众基础。",
        ),
    ]

    # 同义改写增强（仅对部分样本做问题改写，回答保持一致）
    rewrite_templates = [
        "请问{}",
        "{}？请简要说明。",
        "能解释一下{}吗？",
        "关于{}，标准表述是什么？",
    ]

    augmented = []
    for i, item in enumerate(deduped[:20]):
        q = item["messages"][1]["content"].rstrip("？?")
        a = item["messages"][2]["content"]
        tpl = rewrite_templates[i % len(rewrite_templates)]
        new_q = tpl.format(q)
        augmented.append(build_sample(new_q, a))

    all_items = deduped + latest_samples + augmented

    # 二次去重（防止增强后撞车）
    final_items = []
    seen_pair = set()
    for item in all_items:
        q = item["messages"][1]["content"].strip()
        a = item["messages"][2]["content"].strip()
        k = (q, a)
        if k in seen_pair:
            continue
        seen_pair.add(k)
        final_items.append(item)

    rng = random.Random(20260426)
    rng.shuffle(final_items)

    n = len(final_items)
    n_train = int(n * 0.8)
    n_dev = int(n * 0.1)
    n_test = n - n_train - n_dev

    train = final_items[:n_train]
    dev = final_items[n_train : n_train + n_dev]
    test = final_items[n_train + n_dev :]

    write_jsonl(train_path, train)
    write_jsonl(dev_path, dev)
    write_jsonl(test_path, test)

    print(f"total={n}, train={len(train)}, dev={len(dev)}, test={len(test)}")


if __name__ == "__main__":
    main()
