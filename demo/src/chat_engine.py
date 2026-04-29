"""
聊天引擎模块
整合RAG、会话管理和流式文本生成
"""
import time
import logging
import hashlib
from typing import List, Optional, Dict
from threading import Thread

# Mock模式下可能没有torch，使用条件导入
try:
    import torch
    from transformers import (
        StoppingCriteria, 
        StoppingCriteriaList, 
        TextIteratorStreamer
    )
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    # Mock模式的替代类
    class StoppingCriteria:
        pass
    class TextIteratorStreamer:
        def __init__(self, **kwargs):
            pass
        def put(self, token):
            pass
        def end(self):
            pass

from config import settings
from knowledge_base import KnowledgeBase
from cache import answer_cache, retrieval_cache

logger = logging.getLogger(__name__)


class StopOnTokens(StoppingCriteria):
    """自定义停止条件，用于控制生成结束"""
    
    def __init__(self, eos_token_id):
        # 保留原始类型，不转换
        self.eos_token_id = eos_token_id

    def __call__(self, input_ids, scores, **kwargs) -> bool:
        """
        判断是否应该停止生成
        
        Args:
            input_ids: 输入token IDs
            scores: 生成分数
            
        Returns:
            是否应该停止
        """
        if not HAS_TORCH:
            return False
            
        if input_ids.shape[-1] == 0:
            return False
        
        last_token = input_ids[0][-1].item()
        
        if isinstance(self.eos_token_id, (list, tuple)):
            return last_token in self.eos_token_id
        elif torch.is_tensor(self.eos_token_id):
            return last_token in self.eos_token_id.tolist()
        else:
            return last_token == self.eos_token_id


class SessionData:
    """会话数据类"""
    
    def __init__(self):
        self.history: List[List[str]] = []  # [[user_msg, assistant_msg], ...]
        self.last_access: float = time.time()
    
    def add_message(self, user_msg: str, assistant_msg: str):
        """添加对话消息"""
        self.history.append([user_msg, assistant_msg])
        self.last_access = time.time()
        
        # 限制历史长度
        if len(self.history) > settings.session.max_history_length:
            self.history.pop(0)
    
    def is_expired(self) -> bool:
        """检查会话是否过期"""
        return (time.time() - self.last_access) > settings.session.timeout
    
    def clear(self):
        """清空会话历史"""
        self.history.clear()
        self.last_access = time.time()


class ChatEngine:
    """聊天引擎核心类"""
    
    def __init__(self, model, tokenizer, knowledge_base: KnowledgeBase):
        """
        初始化聊天引擎
        
        Args:
            model: 语言模型实例
            tokenizer: 分词器实例
            knowledge_base: 知识库实例
        """
        self.model = model
        self.tokenizer = tokenizer
        self.kb = knowledge_base
        self.sessions: Dict[str, SessionData] = {}
        
        logger.info("聊天引擎初始化完成")
    
    def _get_or_create_session(self, session_id: str) -> SessionData:
        """
        获取或创建会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话数据对象
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionData()
            logger.debug(f"创建新会话: {session_id}")
        
        session = self.sessions[session_id]
        session.last_access = time.time()
        return session
    
    def get_session_history(self, session_id: str) -> List[List[str]]:
        """
        获取会话历史
        
        Args:
            session_id: 会话ID
            
        Returns:
            对话历史列表
        """
        session = self.sessions.get(session_id)
        return session.history.copy() if session else []
    
    def clear_session(self, session_id: str):
        """
        清空指定会话
        
        Args:
            session_id: 会话ID
        """
        if session_id in self.sessions:
            self.sessions[session_id].clear()
            logger.info(f"会话已清空: {session_id}")
        else:
            logger.warning(f"会话不存在: {session_id}")
    
    def generate_response(
        self,
        user_input: str,
        session_id: str = "default",
        system_prompt: Optional[str] = None,
        max_new_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        temperature: Optional[float] = None,
        repetition_penalty: Optional[float] = None,
    ) -> dict:
        """
        根据用户输入生成回答（包含检索增强）
        
        Args:
            user_input: 用户问题
            session_id: 会话ID
            system_prompt: 自定义系统提示
            max_new_tokens: 最大生成token数
            top_p: 核采样参数
            temperature: 温度参数
            repetition_penalty: 重复惩罚参数
            
        Returns:
            包含回答、来源等信息的字典
            
        Raises:
            ValueError: 输入验证失败
            RuntimeError: 生成过程出错
        """
        # 参数验证
        if not user_input or not user_input.strip():
            raise ValueError("问题不能为空")
        
        logger.info(f"处理请求 [session={session_id}]: {user_input[:50]}...")
        
        try:
            # 生成缓存键（基于问题和参数）
            cache_key_params = f"{user_input}|{top_p}|{temperature}|{max_new_tokens}"
            cache_key = f"answer:{hashlib.md5(cache_key_params.encode()).hexdigest()}"
            
            # 尝试从缓存获取
            cached_answer = answer_cache.get(cache_key)
            if cached_answer is not None:
                logger.info(f"📦 答案缓存命中: {user_input[:30]}...")
                # 仍然更新会话历史
                session = self._get_or_create_session(session_id)
                session.add_message(user_input, cached_answer['answer'])
                return {
                    **cached_answer,
                    "session_id": session_id,
                    "history_length": len(session.history),
                    "from_cache": True  # 标记来自缓存
                }
            
            logger.info(f"⚡ 缓存未命中，开始生成...")
            
            # 1. 检索相关知识
            retrieved = self._retrieve_knowledge(user_input)
            context = "\n\n".join(retrieved)
            
            # 2. 获取会话历史
            session = self._get_or_create_session(session_id)
            
            # 3. 构建消息列表
            messages = self._build_messages(
                user_input=user_input,
                context=context,
                history=session.history,
                system_prompt=system_prompt
            )
            
            # 4. 生成回答
            answer = self._generate_text(
                messages=messages,
                max_new_tokens=max_new_tokens,
                top_p=top_p,
                temperature=temperature,
                repetition_penalty=repetition_penalty
            )
            
            # 5. 更新会话历史
            session.add_message(user_input, answer)
            
            result = {
                "answer": answer,
                "sources": retrieved,
                "session_id": session_id,
                "retrieved_count": len(retrieved),
                "history_length": len(session.history),
                "from_cache": False
            }
            
            # 6. 存入缓存
            answer_cache.set(cache_key, result)
            logger.debug(f"📦 答案已缓存: {user_input[:30]}...")
            
            logger.info(
                f"回答生成完成 [session={session_id}]: "
                f"{len(answer)} 字符, {len(retrieved)} 个来源"
            )
            
            return result
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"生成回答失败 [session={session_id}]: {e}", exc_info=True)
            raise RuntimeError(f"生成回答时出错: {e}")
    
    def _retrieve_knowledge(self, query: str) -> List[str]:
        """
        从知识库检索相关知识（带缓存）
        
        Args:
            query: 查询文本
            
        Returns:
            相关段落列表
        """
        # 生成缓存键
        cache_key = f"retrieval:{query}"
        
        # 尝试从缓存获取
        cached_result = retrieval_cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"📦 检索结果缓存命中: {query[:30]}...")
            return cached_result
        
        # 缓存未命中，执行检索
        start_time = time.time()
        try:
            retrieved = self.kb.retrieve(query, k=settings.retrieval.k)
            duration = time.time() - start_time
            
            # 存入缓存
            if retrieved:
                retrieval_cache.set(cache_key, retrieved)
                logger.debug(
                    f"📦 检索结果已缓存: {query[:30]}... "
                    f"({len(retrieved)} 条, {duration:.3f}s)"
                )
            
            return retrieved
        except Exception as e:
            logger.error(f"检索失败: {e}")
            raise RuntimeError(f"知识库检索出错: {e}")
    
    def _build_messages(
        self,
        user_input: str,
        context: str,
        history: List[List[str]],
        system_prompt: Optional[str] = None
    ) -> List[dict]:
        """
        构建消息列表
        
        Args:
            user_input: 当前用户输入
            context: 检索到的上下文
            history: 对话历史
            system_prompt: 系统提示
            
        Returns:
            消息列表
        """
        # 构建系统消息
        system_content = f"请基于以下已知信息回答问题：\n{context}"
        if system_prompt and system_prompt.strip():
            system_content = f"{system_prompt.strip()}\n\n已知信息：\n{context}"
        
        messages = [{"role": "system", "content": system_content}]
        
        # 添加历史对话
        for user_msg, assistant_msg in history:
            if user_msg:
                messages.append({"role": "user", "content": user_msg})
            if assistant_msg:
                messages.append({"role": "assistant", "content": assistant_msg})
        
        # 添加当前问题
        messages.append({"role": "user", "content": user_input})
        
        return messages
    
    def _generate_text(
        self,
        messages: List[dict],
        max_new_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        temperature: Optional[float] = None,
        repetition_penalty: Optional[float] = None,
    ) -> str:
        """
        使用模型生成文本
        
        Args:
            messages: 消息列表
            max_new_tokens: 最大生成token数
            top_p: 核采样参数
            temperature: 温度参数
            repetition_penalty: 重复惩罚参数
            
        Returns:
            生成的文本
        """
        # 转换为模型输入
        # 【最终修复】：使用标准的 GLM-4 对话模板格式
        
        # 1. 构建符合 GLM-4 规范的 prompt
        prompt_str = ""
        for msg in messages:
            role = msg['role']
            content = msg['content']
            if role == 'system':
                prompt_str += f"<|system|>\n{content}\n"
            elif role == 'user':
                prompt_str += f"<|user|>\n{content}\n"
            elif role == 'assistant':
                prompt_str += f"<|assistant|>\n{content}\n"
        
        # 关键：最后必须加上 <|assistant|>\n 引导模型开始回答
        prompt_str += "<|assistant|>\n"

        # 2. Tokenize
        model_inputs = self.tokenizer(
            [prompt_str], 
            return_tensors="pt", 
            add_special_tokens=False # GLM-4 模板已包含特殊 token，不需要额外添加
        ).to(self.model.device)
        
        # 创建流式输出器
        if HAS_TORCH:
            streamer = TextIteratorStreamer(
                tokenizer=self.tokenizer,
                skip_prompt=True, # 跳过输入的 prompt，只返回新生成的内容
                skip_special_tokens=True, # 跳过 <|user|> 等特殊符号
                timeout=60
            )
            
            # 3. 启动生成线程
            generation_kwargs = dict(
                inputs=model_inputs['input_ids'],
                attention_mask=model_inputs.get('attention_mask', None),
                streamer=streamer,
                max_new_tokens=512,
                do_sample=True,
                temperature=0.8,
                top_p=0.9,
                repetition_penalty=1.1, # 增加重复惩罚，防止复读
                eos_token_id=[self.tokenizer.eos_token_id, self.tokenizer.convert_tokens_to_ids("<|user|>")], # 遇到 <|user|> 也停止
                pad_token_id=self.tokenizer.pad_token_id if self.tokenizer.pad_token_id is not None else self.tokenizer.eos_token_id
            )
            
            thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
            thread.start()
            
            # 4. 收集输出
            answer = ""
            for new_text in streamer:
                answer += new_text
                
            thread.join()
            return answer.strip()
        else:
            # Mock模式：使用简单的列表收集输出
            streamer = []
        
        # 准备生成参数
        generate_kwargs = {
            "input_ids": model_inputs,
            "streamer": streamer,
            "max_new_tokens": max_new_tokens or settings.generation.max_new_tokens,
            "do_sample": True,
            "top_p": top_p if top_p is not None else settings.generation.top_p,
            "temperature": temperature if temperature is not None else settings.generation.temperature,
            "repetition_penalty": repetition_penalty if repetition_penalty is not None else settings.generation.repetition_penalty,
            "eos_token_id": self.model.config.eos_token_id,
        }
        
        # 在单独线程中生成
        if HAS_TORCH:
            thread = Thread(target=self.model.generate, kwargs=generate_kwargs)
            thread.start()
            
            # 收集输出
            full_response = ""
            try:
                for new_token in streamer:
                    if new_token:
                        full_response += new_token
            except Exception as e:
                logger.error(f"流式生成中断: {e}")
                raise RuntimeError(f"生成回答时出错: {e}")
        else:
            # Mock模式：直接调用模型获取回答
            import time
            time.sleep(0.5)  # 模拟延迟
            full_response = self.model._get_mock_response()
        
        return full_response.strip()
    
    def cleanup_expired_sessions(self):
        """清理超时会话"""
        expired = [
            sid for sid, session in self.sessions.items()
            if session.is_expired()
        ]
        
        for sid in expired:
            del self.sessions[sid]
        
        if expired:
            logger.info(
                f"清理了 {len(expired)} 个过期会话，"
                f"当前会话数: {len(self.sessions)}"
            )
    
    def get_stats(self) -> dict:
        """
        获取引擎统计信息
        
        Returns:
            统计信息字典
        """
        return {
            'active_sessions': len(self.sessions),
            'kb_stats': self.kb.get_stats(),
        }