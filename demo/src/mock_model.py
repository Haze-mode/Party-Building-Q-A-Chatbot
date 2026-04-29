"""
Mock模型模块
用于在没有真实模型的情况下进行本地调试
提供模拟的模型行为和响应
"""
import time
import logging
from typing import List, Optional
from threading import Thread

logger = logging.getLogger(__name__)


class MockTokenizer:
    """模拟分词器"""
    
    def __init__(self):
        self.model_max_length = 8192
        logger.info("MockTokenizer 初始化完成")
    
    def apply_chat_template(self, messages, add_generation_prompt=True, tokenize=True, return_tensors="pt"):
        """模拟应用聊天模板"""
        logger.debug(f"应用聊天模板，消息数: {len(messages)}")
        
        # 返回一个模拟的tensor
        class MockTensor:
            def __init__(self):
                self.shape = (1, 100)  # 模拟形状
            
            def to(self, device):
                return self
        
        return MockTensor()
    
    @property
    def eos_token_id(self):
        """返回结束符ID"""
        return 2


class MockModel:
    """模拟语言模型"""
    
    def __init__(self):
        self.device = "cpu"
        self.config = type('obj', (object,), {'eos_token_id': 2})()
        logger.info("MockModel 初始化完成")
    
    def eval(self):
        """设置为评估模式"""
        pass
    
    def generate(self, input_ids, streamer, max_new_tokens=100, **kwargs):
        """
        模拟文本生成
        根据用户问题返回预设的回答
        """
        try:
            # 模拟生成延迟
            time.sleep(0.5)
            
            # 获取模拟回答
            response = self._get_mock_response()
            
            # 逐字输出（模拟流式）
            for char in response:
                streamer.put(char)
                time.sleep(0.02)  # 模拟逐字输出延迟
            
            streamer.end()
            logger.info(f"Mock模型生成完成，长度: {len(response)}")
            
        except Exception as e:
            logger.error(f"Mock生成失败: {e}")
            streamer.end()
    
    def _get_mock_response(self) -> str:
        """
        根据上下文返回模拟回答
        这里可以添加更多智能回复逻辑
        """
        # 可以从最近的对话中获取一些上下文
        mock_responses = [
            "这是一个很好的问题！基于我的知识，我可以这样回答：\n\n"
            "首先，这个概念涉及到多个方面。让我详细解释一下...\n\n"
            "1. **基本概念**：这是指一种重要的技术或方法\n"
            "2. **应用场景**：在实际工作中有很多用途\n"
            "3. **最佳实践**：建议按照标准流程操作\n\n"
            "希望这个回答对您有帮助！如果还有疑问，欢迎继续提问。",
            
            "感谢您的提问！让我来解答：\n\n"
            "根据相关知识库的内容，这个问题可以从以下几个角度理解：\n\n"
            "• **理论层面**：有明确的概念定义\n"
            "• **实践层面**：需要结合具体情况\n"
            "• **发展趋势**：未来会有更多应用\n\n"
            "建议您参考相关文档获取更详细的信息。",
            
            "好问题！我来为您详细说明：\n\n"
            "这个话题确实值得深入探讨。简单来说：\n\n"
            "**核心要点**：\n"
            "- 第一点很重要\n"
            "- 第二点需要注意\n"
            "- 第三点是关键\n\n"
            "总结：这是一个复杂但有价值的话题，建议持续学习和实践。",
            
            "很高兴为您解答！\n\n"
            "关于这个问题，我的看法是：\n\n"
            "从专业角度来看，这需要综合考虑多方面因素。\n"
            "在实际应用中，我们通常会采用以下策略：\n\n"
            "1. 分析需求\n"
            "2. 设计方案\n"
            "3. 实施验证\n"
            "4. 优化改进\n\n"
            "每个步骤都很重要，缺一不可。",
            
            "让我想想... 这是一个很有深度的问题！\n\n"
            "根据我的理解：\n\n"
            "**定义**：这是指某种特定的现象或方法\n"
            "**特点**：具有独特的优势和局限性\n"
            "**应用**：在多个领域都有广泛应用\n\n"
            "如果您需要更专业的建议，建议咨询相关领域的专家。"
        ]
        
        # 随机选择一个回答（实际可以根据问题内容选择）
        import random
        return random.choice(mock_responses)


def load_mock_model_and_tokenizer():
    """
    加载模拟模型和分词器
    
    Returns:
        (model, tokenizer) 元组
    """
    logger.info("=" * 60)
    logger.info("🎭 正在加载 Mock 模型（调试模式）")
    logger.info("=" * 60)
    
    model = MockModel()
    tokenizer = MockTokenizer()
    
    logger.info("✅ Mock 模型加载完成")
    logger.info("⚠️  注意：当前使用模拟回答，非真实AI生成")
    logger.info("=" * 60)
    
    return model, tokenizer


if __name__ == '__main__':
    # 测试Mock模型
    logging.basicConfig(level=logging.INFO)
    
    print("\n=== 测试 Mock 模型 ===\n")
    
    model, tokenizer = load_mock_model_and_tokenizer()
    
    # 测试生成
    from transformers import TextIteratorStreamer
    
    messages = [
        {"role": "system", "content": "你是一个助手"},
        {"role": "user", "content": "你好"}
    ]
    
    model_inputs = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=True,
        return_tensors="pt"
    )
    
    streamer = TextIteratorStreamer(
        tokenizer=tokenizer,
        timeout=60,
        skip_prompt=True,
        skip_special_tokens=True
    )
    
    thread = Thread(target=model.generate, kwargs={
        "input_ids": model_inputs,
        "streamer": streamer,
        "max_new_tokens": 100
    })
    thread.start()
    
    print("\n生成的回答：")
    print("-" * 60)
    for token in streamer:
        print(token, end='', flush=True)
    print("\n" + "-" * 60)
    print("\n✅ 测试完成！")
