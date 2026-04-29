#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据集是否有泄露
"""
import json

def load_questions(file_path):
    """加载问题列表"""
    questions = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                questions.append(data['messages'][1]['content'])
    return set(questions)

# 加载三个数据集的问题
train_q = load_questions('train.jsonl')
test_q = load_questions('test.jsonl')
dev_q = load_questions('dev.jsonl')

print("="*80)
print("数据集泄露检查")
print("="*80)
print(f"\n训练集问题数: {len(train_q)}")
print(f"测试集问题数: {len(test_q)}")
print(f"验证集问题数: {len(dev_q)}")

# 检查重叠
overlap_train_test = train_q & test_q
overlap_train_dev = train_q & dev_q
overlap_test_dev = test_q & dev_q

print(f"\n训练&测试重叠: {len(overlap_train_test)}条")
print(f"训练&验证重叠: {len(overlap_train_dev)}条")
print(f"测试&验证重叠: {len(overlap_test_dev)}条")

print("\n" + "="*80)
print("检查结果")
print("="*80)

if overlap_train_test:
    print("\n❌ 严重问题：训练集和测试集有重叠！")
    print("重叠的问题示例：")
    for i, q in enumerate(list(overlap_train_test)[:5], 1):
        print(f"  {i}. {q[:80]}...")
    print("\n这会导致评估结果虚高（数据泄露）！")
elif overlap_train_dev:
    print("\n⚠️  警告：训练集和验证集有重叠！")
    print("这会影响早停策略的效果。")
elif overlap_test_dev:
    print("\n⚠️  警告：测试集和验证集有重叠！")
else:
    print("\n✅ 数据集划分正确，无重叠！")

# 显示一些样本
print("\n" + "="*80)
print("测试集前3条问题（应该在训练集中不存在）")
print("="*80)
test_list = list(test_q)[:3]
for i, q in enumerate(test_list, 1):
    in_train = "❌ 在训练集中存在！" if q in train_q else "✅ 不在训练集中"
    print(f"\n{i}. {q}")
    print(f"   {in_train}")
