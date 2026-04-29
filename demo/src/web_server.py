"""
Web服务器主入口
基于Tornado框架提供REST API服务
支持Mock模式用于本地调试（无需真实模型）
"""
import os
import logging
import time
import tornado.ioloop
from tornado.ioloop import PeriodicCallback

from config import settings
from knowledge_base import KnowledgeBase
from chat_engine import ChatEngine
from api_handlers import create_handlers
from cache import init_cache_cleanup_task

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.logging.level),
    format=settings.logging.format
)
logger = logging.getLogger(__name__)


def initialize_components(use_mock=False):
    """
    初始化所有核心组件
    
    Args:
        use_mock: 是否使用Mock模式（无需真实模型）
        
    Returns:
        (model, tokenizer, kb, chat_engine) 元组
    """
    logger.info("="*60)
    logger.info("GLM-4 问答服务启动中...")
    if use_mock:
        logger.info("🎭 模式: Mock调试模式（无需真实模型）")
    else:
        logger.info("🤖 模式: 真实模型模式")
    logger.info("="*60)
    
    # 1. 加载模型
    if use_mock:
        # 使用Mock模型
        from mock_model import load_mock_model_and_tokenizer
        logger.info("正在加载 Mock 模型...")
        try:
            model, tokenizer = load_mock_model_and_tokenizer()
            logger.info("✓ Mock模型加载完成")
        except Exception as e:
            logger.error(f"Mock模型加载失败: {e}", exc_info=True)
            raise
    else:
        # 使用真实模型
        from model_loader import load_model_and_tokenizer
        logger.info(f"正在加载模型: {settings.model.path}")
        try:
            model, tokenizer = load_model_and_tokenizer(
                settings.model.path,
                trust_remote_code=settings.model.trust_remote_code
            )
            model.eval()
            logger.info("✓ 模型加载完成")
        except Exception as e:
            logger.error(f"模型加载失败: {e}", exc_info=True)
            raise
    
    # 2. 初始化知识库
    logger.info(f"正在加载知识库: {settings.kb.directory}")
    try:
        kb = KnowledgeBase(settings.kb.directory)
        logger.info(f"✓ 知识库加载完成 ({len(kb)} 个段落)")
    except Exception as e:
        logger.error(f"知识库加载失败: {e}", exc_info=True)
        raise
    
    # 3. 创建聊天引擎
    logger.info("正在初始化聊天引擎...")
    chat_engine = ChatEngine(model, tokenizer, kb)
    logger.info("✓ 聊天引擎初始化完成")
    
    logger.info("="*60)
    logger.info("所有组件初始化完成！")
    logger.info("="*60)
    
    return model, tokenizer, kb, chat_engine


def create_application(chat_engine, kb):
    """
    创建Tornado应用
    
    Args:
        chat_engine: 聊天引擎实例
        kb: 知识库实例
        
    Returns:
        Tornado Application实例
    """
    handlers = create_handlers(chat_engine, kb)
    
    # 配置CORS
    settings_dict = {
        'default_handler_class': tornado.web.RequestHandler,
        'cors_allow_origin': '*',
        'cors_allow_methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'cors_allow_headers': 'Content-Type, Authorization, X-Requested-With',
        'cors_allow_credentials': True,
    }
    
    app = tornado.web.Application(handlers, **settings_dict)
    
    # 添加CORS中间件
    def cors_middleware(handler, method):
        """CORS中间件"""
        handler.set_header("Access-Control-Allow-Origin", "*")
        handler.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        handler.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        handler.set_header("Access-Control-Allow-Credentials", "true")
        
        # 处理OPTIONS预检请求
        if method == "OPTIONS":
            handler.set_status(204)
            handler.finish()
            return True
        return False
    
    # 重写prepare方法添加CORS支持
    original_prepare = tornado.web.RequestHandler.prepare
    
    def new_prepare(self):
        cors_middleware(self, self.request.method)
        return original_prepare(self)
    
    tornado.web.RequestHandler.prepare = new_prepare
    
    # 添加性能监控中间件
    original_execute = tornado.web.RequestHandler._execute
    
    async def monitored_execute(self, transforms, *args, **kwargs):
        """性能监控：记录每个请求的执行时间"""
        start_time = time.time()
        try:
            await original_execute(self, transforms, *args, **kwargs)
        finally:
            duration = time.time() - start_time
            method = self.request.method
            uri = self.request.uri
            status = self.get_status()
            
            # 慢请求告警（超过1秒）
            if duration > 1.0:
                logger.warning(
                    f"⚠️  慢请求: {method} {uri} - {status} - {duration:.3f}s"
                )
            elif duration > 0.1:
                logger.info(
                    f"📊 请求耗时: {method} {uri} - {status} - {duration:.3f}s"
                )
    
    tornado.web.RequestHandler._execute = monitored_execute
    
    return app


def start_server(use_mock=False):
    """
    启动Web服务器
    
    Args:
        use_mock: 是否使用Mock模式
    """
    # 初始化组件
    model, tokenizer, kb, chat_engine = initialize_components(use_mock=use_mock)
    
    # 创建应用
    app = create_application(chat_engine, kb)
    
    # 监听端口
    app.listen(settings.server.port, address=settings.server.host)
    
    # 打印启动信息
    logger.info("")
    logger.info("🚀 服务已启动！")
    logger.info(f"📍 地址: http://{settings.server.host}:{settings.server.port}")
    logger.info(f"💬 聊天接口: http://localhost:{settings.server.port}/api/chatbot")
    logger.info(f"🔑 登录接口: http://localhost:{settings.server.port}/api/login")
    logger.info("")
    logger.info("默认用户:")
    logger.info("  - 管理员: admin / admin123")
    logger.info("  - 普通用户: user / user123")
    logger.info("")
    logger.info("可用接口:")
    logger.info("  - POST /api/login - 用户登录")
    logger.info("  - POST /api/logout - 用户登出")
    logger.info("  - GET/POST /api/chatbot - 发送问题")
    logger.info("  - GET /api/session/history - 获取会话历史")
    logger.info("  - GET /api/session/clear - 清空会话")
    logger.info("  - GET /api/session/list - 获取会话列表")
    logger.info("  - GET/POST /api/kb/reload - 重载知识库（需管理员）")
    logger.info("  - POST /api/kb/upload - 上传文件（需管理员）")
    logger.info("")
    
    # 启动定时清理任务
    cleanup_task = PeriodicCallback(
        chat_engine.cleanup_expired_sessions,
        settings.session.cleanup_interval
    )
    cleanup_task.start()
    logger.info(f"✓ 会话清理任务已启动 (间隔: {settings.session.cleanup_interval/1000}秒)")
    
    # 启动缓存清理任务
    init_cache_cleanup_task(interval=300)  # 每5分钟清理一次
    
    # 启动事件循环
    try:
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        logger.info("")
        logger.info("服务已停止")


if __name__ == '__main__':
    # 检查是否启用Mock模式
    use_mock = os.environ.get('USE_MOCK', '').lower() in ['1', 'true', 'yes']
    
    if use_mock:
        logger.info("🎭 检测到 USE_MOCK 环境变量，启用Mock调试模式")
    
    start_server(use_mock=use_mock)