"""
系统配置模块
提供集中化的配置管理，支持环境变量覆盖
"""
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModelConfig:
    """模型配置"""
    path: str = field(
        default_factory=lambda: os.environ.get(
            'MODEL_PATH', 
            '/root/GLM-4/finetune_demo/output/checkpoint-2950'
        )
    )
    trust_remote_code: bool = True


@dataclass
class GenerationConfig:
    """文本生成配置"""
    max_new_tokens: int = 8192
    top_p: float = 0.7
    temperature: float = 0.9
    repetition_penalty: float = 1.2


@dataclass
class RetrievalConfig:
    """检索配置"""
    k: int = 3  # 返回的段落数量


@dataclass
class SessionConfig:
    """会话管理配置"""
    max_history_length: int = 10  # 每会话最大对话轮数
    timeout: int = 3600  # 会话超时时间（秒）
    cleanup_interval: int = 3600 * 1000  # 清理间隔（毫秒）


@dataclass
class KnowledgeBaseConfig:
    """知识库配置"""
    directory: str = field(
        default_factory=lambda: os.environ.get('KB_DIR', '/root/GLM-4/demo/data/示例知识库')
    )  # 使用data目录下的示例知识库
    chunk_size: int = 500  # 文档分割大小
    chunk_overlap: int = 50  # 分割重叠大小
    supported_formats: list = field(default_factory=lambda: ['.txt', '.pdf', '.docx'])


@dataclass
class ServerConfig:
    """服务器配置"""
    port: int = 6006  # 使用6006端口
    host: str = '0.0.0.0'


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = 'INFO'
    format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


class Settings:
    """
    全局配置管理类
    提供统一的配置访问接口
    """
    
    def __init__(self):
        self.model = ModelConfig()
        self.generation = GenerationConfig()
        self.retrieval = RetrievalConfig()
        self.session = SessionConfig()
        self.kb = KnowledgeBaseConfig()
        self.server = ServerConfig()
        self.logging = LoggingConfig()
    
    @property
    def MODEL_PATH(self) -> str:
        """兼容旧代码的MODEL_PATH属性"""
        return self.model.path
    
    @property
    def KB_DIR(self) -> str:
        """兼容旧代码的KB_DIR属性"""
        return self.kb.directory
    
    @property
    def MAX_NEW_TOKENS(self) -> int:
        """兼容旧代码的MAX_NEW_TOKENS属性"""
        return self.generation.max_new_tokens
    
    @property
    def TOP_P(self) -> float:
        """兼容旧代码的TOP_P属性"""
        return self.generation.top_p
    
    @property
    def TEMPERATURE(self) -> float:
        """兼容旧代码的TEMPERATURE属性"""
        return self.generation.temperature
    
    @property
    def REPETITION_PENALTY(self) -> float:
        """兼容旧代码的REPETITION_PENALTY属性"""
        return self.generation.repetition_penalty
    
    @property
    def RETRIEVAL_K(self) -> int:
        """兼容旧代码的RETRIEVAL_K属性"""
        return self.retrieval.k
    
    @property
    def MAX_HISTORY_LENGTH(self) -> int:
        """兼容旧代码的MAX_HISTORY_LENGTH属性"""
        return self.session.max_history_length
    
    @property
    def SESSION_TIMEOUT(self) -> int:
        """兼容旧代码的SESSION_TIMEOUT属性"""
        return self.session.timeout
    
    @property
    def WEB_PORT(self) -> int:
        """兼容旧代码的WEB_PORT属性"""
        return self.server.port
    
    def update_from_env(self):
        """从环境变量更新配置"""
        if 'MODEL_PATH' in os.environ:
            self.model.path = os.environ['MODEL_PATH']
        if 'KB_DIR' in os.environ:
            self.kb.directory = os.environ['KB_DIR']
        if 'WEB_PORT' in os.environ:
            try:
                self.server.port = int(os.environ['WEB_PORT'])
            except ValueError:
                pass
    
    def to_dict(self) -> dict:
        """将配置转换为字典（用于调试）"""
        return {
            'model': vars(self.model),
            'generation': vars(self.generation),
            'retrieval': vars(self.retrieval),
            'session': vars(self.session),
            'kb': vars(self.kb),
            'server': vars(self.server),
            'logging': vars(self.logging),
        }


# 全局配置实例
settings = Settings()

# 为了向后兼容，导出常用配置项
MODEL_PATH = settings.MODEL_PATH
KB_DIR = settings.KB_DIR
MAX_NEW_TOKENS = settings.MAX_NEW_TOKENS
TOP_P = settings.TOP_P
TEMPERATURE = settings.TEMPERATURE
REPETITION_PENALTY = settings.REPETITION_PENALTY
RETRIEVAL_K = settings.RETRIEVAL_K
MAX_HISTORY_LENGTH = settings.MAX_HISTORY_LENGTH
SESSION_TIMEOUT = settings.SESSION_TIMEOUT
WEB_PORT = settings.WEB_PORT
import os

# 读取环境变量，如果没有设置，则使用默认值（第二个参数）
MODEL_PATH = os.getenv('MODEL_PATH', '/root/models/glm-4-9b-chat')
KB_DIR = os.getenv('KB_DIR', '/root/GLM-4/demo/data/示例知识库')
WEB_PORT = os.getenv('WEB_PORT', '6006')

# 这样，无论你在终端里 export 了什么值，这里都能读到
# 如果终端没 export，这里就用默认值，不会报错