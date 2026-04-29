#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新划分数据集，确保训练集、验证集、测试集完全无重叠
按照 7:2:1 的比例划分
"""
import json
import random

def load_all_data():
    """加载所有数据，去重"""
    all_questions = {}  # {question: answer}
    
    # 从三个文件加载
    for file in ['train.jsonl', 'test.jsonl', 'dev.jsonl']:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        question = data['messages'][1]['content']
                        answer = data['messages'][2]['content']
                        system = data['messages'][0]['content']
                        
                        # 使用问题作为key，确保唯一
                        if question not in all_questions:
                            all_questions[question] = {
                                'system': system,
                                'question': question,
                                'answer': answer
                            }
        except FileNotFoundError:
            print(f"警告：{file} 不存在，跳过")
    
    return list(all_questions.values())

def split_dataset(data, train_ratio=0.65, val_ratio=0.2, test_ratio=0.15):
    """按比例划分数据集
    
    默认比例：65% 训练, 20% 验证, 15% 测试
    这样可以确保测试集有足够的数据进行可靠评估
    """
    # 随机打乱
    random.shuffle(data)
    
    total = len(data)
    train_end = int(total * train_ratio)
    val_end = int(total * (train_ratio + val_ratio))
    
    train_data = data[:train_end]
    val_data = data[train_end:val_end]
    test_data = data[val_end:]
    
    return train_data, val_data, test_data

def save_dataset(data, filename):
    """保存数据集"""
    with open(filename, 'w', encoding='utf-8') as f:
        for item in data:
            record = {
                "messages": [
                    {"role": "system", "content": item['system']},
                    {"role": "user", "content": item['question']},
                    {"role": "assistant", "content": item['answer']}
                ]
            }
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    print(f"已保存 {filename}: {len(data)}条")

def verify_no_overlap(train_file, val_file, test_file):
    """验证无重叠"""
    def load_questions(file):
        questions = set()
        with open(file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    questions.add(data['messages'][1]['content'])
        return questions
    
    train_q = load_questions(train_file)
    val_q = load_questions(val_file)
    test_q = load_questions(test_file)
    
    overlap_tv = train_q & val_q
    overlap_tt = train_q & test_q
    overlap_vt = val_q & test_q
    
    print("\n" + "="*80)
    print("验证结果")
    print("="*80)
    print(f"训练集: {len(train_q)}条")
    print(f"验证集: {len(val_q)}条")
    print(f"测试集: {len(test_q)}条")
    print(f"\n训练&验证重叠: {len(overlap_tv)}条")
    print(f"训练&测试重叠: {len(overlap_tt)}条")
    print(f"验证&测试重叠: {len(overlap_vt)}条")
    
    if overlap_tv or overlap_tt or overlap_vt:
        print("\n❌ 仍有重叠！")
        return False
    else:
        print("\n✅ 数据集完全无重叠！")
        return True

def main():
    print("="*80)
    print("重新划分数据集（确保无重叠）")
    print("="*80)
    
    # 加载所有数据
    print("\n正在加载数据...")
    all_data = load_all_data()
    print(f"总共加载 {len(all_data)} 条唯一数据")
    
    if len(all_data) < 10:
        print("错误：数据太少，无法划分")
        return
    
    # 划分数据集
    print("\n正在划分数据集...")
    train_data, val_data, test_data = split_dataset(all_data)
    
    print(f"训练集: {len(train_data)}条 ({len(train_data)/len(all_data)*100:.1f}%)")
    print(f"验证集: {len(val_data)}条 ({len(val_data)/len(all_data)*100:.1f}%)")
    print(f"测试集: {len(test_data)}条 ({len(test_data)/len(all_data)*100:.1f}%)")
    
    # 备份旧文件
    import os
    import shutil
    backup_dir = 'backup_old_datasets'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        for file in ['train.jsonl', 'test.jsonl', 'dev.jsonl']:
            if os.path.exists(file):
                shutil.copy(file, os.path.join(backup_dir, file))
        print(f"\n已备份旧数据到 {backup_dir}/")
    
    # 保存新文件
    print("\n正在保存新数据集...")
    save_dataset(train_data, 'train.jsonl')
    save_dataset(val_data, 'dev.jsonl')
    save_dataset(test_data, 'test.jsonl')
    
    # 验证
    print("\n正在验证...")
    verify_no_overlap('train.jsonl', 'dev.jsonl', 'test.jsonl')
    
    print("\n" + "="*80)
    print("完成！")
    print("="*80)
    print("\n⚠️  重要提示：")
    print("1. 旧数据已备份到 backup_old_datasets/ 目录")
    print("2. 请重新运行训练脚本")
    print("3. 使用新的数据进行评估")

if __name__ == '__main__':
    main()
