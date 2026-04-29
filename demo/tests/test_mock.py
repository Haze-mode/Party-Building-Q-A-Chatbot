"""
Mock模型简单测试
不依赖transformers库，直接测试核心功能
"""
import sys
import time
from mock_model import MockModel, MockTokenizer, load_mock_model_and_tokenizer

def test_mock_model():
    """测试Mock模型基本功能"""
    
    print("\n" + "="*60)
    print("🧪 Mock 模型功能测试")
    print("="*60 + "\n")
    
    # 1. 测试初始化
    print("1️⃣  测试模型初始化...")
    try:
        model = MockModel()
        tokenizer = MockTokenizer()
        print("   ✅ 模型和分词器初始化成功\n")
    except Exception as e:
        print(f"   ❌ 初始化失败: {e}\n")
        return False
    
    # 2. 测试分词器
    print("2️⃣  测试分词器...")
    try:
        messages = [
            {"role": "system", "content": "你是一个助手"},
            {"role": "user", "content": "你好"}
        ]
        result = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_tensors="pt"
        )
        print(f"   ✅ 分词器工作正常，返回形状: {result.shape}\n")
    except Exception as e:
        print(f"   ❌ 分词器测试失败: {e}\n")
        return False
    
    # 3. 测试模型生成
    print("3️⃣  测试模型生成（模拟流式输出）...")
    try:
        class SimpleStreamer:
            def __init__(self):
                self.output = []
            
            def put(self, token):
                self.output.append(token)
                print(token, end='', flush=True)
            
            def end(self):
                pass
        
        streamer = SimpleStreamer()
        
        print("\n   生成的回答：")
        print("   " + "-"*56)
        print("   ", end='')
        
        start_time = time.time()
        model.generate(
            input_ids=None,
            streamer=streamer,
            max_new_tokens=100
        )
        elapsed = time.time() - start_time
        
        print("\n   " + "-"*56)
        print(f"\n   ✅ 生成完成！耗时: {elapsed:.2f}秒")
        print(f"   📝 生成长度: {len(''.join(streamer.output))} 字符\n")
        
    except Exception as e:
        print(f"\n   ❌ 生成测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. 测试加载函数
    print("4️⃣  测试load_mock_model_and_tokenizer函数...")
    try:
        model, tokenizer = load_mock_model_and_tokenizer()
        print("   ✅ 加载函数工作正常\n")
    except Exception as e:
        print(f"   ❌ 加载函数失败: {e}\n")
        return False
    
    print("="*60)
    print("✅ 所有测试通过！Mock模型可以正常使用")
    print("="*60 + "\n")
    
    return True


if __name__ == '__main__':
    success = test_mock_model()
    sys.exit(0 if success else 1)
