"""
用户认证模块
提供用户验证、Token管理和权限控制功能
"""
import hashlib
import uuid
import logging
from functools import wraps
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class User:
    """用户信息类"""
    
    def __init__(self, username: str, role: str):
        self.username = username
        self.role = role
    
    def to_dict(self) -> dict:
        return {
            'username': self.username,
            'role': self.role
        }


class AuthService:
    """认证服务类"""
    
    # 默认用户数据库（生产环境建议使用数据库）
    DEFAULT_USERS = {
        'admin': {
            'password_hash': hashlib.sha256('admin123'.encode()).hexdigest(),
            'role': 'admin'
        },
        'user': {
            'password_hash': hashlib.sha256('user123'.encode()).hexdigest(),
            'role': 'user'
        }
    }
    
    def __init__(self):
        self.users = self.DEFAULT_USERS.copy()
        self.active_sessions: Dict[str, User] = {}  # token -> User
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        验证用户凭据
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            User对象如果验证成功，否则返回None
        """
        user_data = self.users.get(username)
        if not user_data:
            logger.warning(f"用户不存在: {username}")
            return None
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if user_data['password_hash'] != password_hash:
            logger.warning(f"密码错误: {username}")
            return None
        
        logger.info(f"用户登录成功: {username}")
        return User(username=username, role=user_data['role'])
    
    def generate_token(self) -> str:
        """生成唯一的会话Token"""
        return str(uuid.uuid4())
    
    def login(self, username: str, password: str) -> tuple:
        """
        用户登录
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            (success: bool, token: str, user: User, error: str)
        """
        user = self.authenticate(username, password)
        if not user:
            return False, None, None, "用户名或密码错误"
        
        token = self.generate_token()
        self.active_sessions[token] = user
        logger.info(f"用户 {username} 登录成功，token: {token[:8]}...")
        
        return True, token, user, None
    
    def logout(self, token: str) -> bool:
        """
        用户登出
        
        Args:
            token: 会话Token
            
        Returns:
            是否成功登出
        """
        if token in self.active_sessions:
            user = self.active_sessions.pop(token)
            logger.info(f"用户 {user.username} 已登出")
            return True
        return False
    
    def verify_token(self, token: str) -> Optional[User]:
        """
        验证Token有效性
        
        Args:
            token: 会话Token
            
        Returns:
            User对象如果Token有效，否则返回None
        """
        return self.active_sessions.get(token)
    
    def require_role(self, token: str, required_role: str) -> tuple:
        """
        检查用户是否具有指定角色
        
        Args:
            token: 会话Token
            required_role: 所需角色
            
        Returns:
            (success: bool, user: User, error: str)
        """
        user = self.verify_token(token)
        if not user:
            return False, None, "无效Token"
        
        if user.role != required_role:
            return False, None, f"需要 {required_role} 权限"
        
        return True, user, None
    
    def get_session_count(self) -> int:
        """获取活跃会话数量"""
        return len(self.active_sessions)
    
    def cleanup_expired_sessions(self, session_manager):
        """
        清理超时会话（委托给session_manager）
        
        Args:
            session_manager: 会话管理器实例
        """
        if session_manager:
            session_manager.cleanup_expired_sessions()


# 全局认证服务实例
auth_service = AuthService()


def require_auth(role: Optional[str] = None):
    """
    认证装饰器
    
    Args:
        role: 所需角色，None表示只需登录
    """
    def decorator(func):
        @wraps(func)
        def wrapper(handler, *args, **kwargs):
            auth_header = handler.request.headers.get('Authorization', '')
            
            if not auth_header.startswith('Bearer '):
                handler.set_status(401)
                handler.write({'error': '需要认证'})
                return
            
            token = auth_header[7:]  # Remove 'Bearer '
            user = auth_service.verify_token(token)
            
            if not user:
                handler.set_status(401)
                handler.write({'error': '无效Token'})
                return
            
            if role and user.role != role:
                handler.set_status(403)
                handler.write({'error': f'需要 {role} 权限'})
                return
            
            handler.current_user = user
            return func(handler, *args, **kwargs)
        
        return wrapper
    return decorator
