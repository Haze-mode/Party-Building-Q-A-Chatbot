"""
缓存模块 - 提升系统性能
支持内存缓存和TTL过期策略
"""
import time
import hashlib
import logging
from typing import Any, Optional
from collections import OrderedDict

logger = logging.getLogger(__name__)


class LRUCache:
    """
    LRU（最近最少使用）缓存实现
    
    特性：
    - 固定容量，自动淘汰最久未使用的数据
    - 支持TTL过期
    - 线程安全
    """
    
    def __init__(self, capacity: int = 1000, default_ttl: int = 3600):
        """
        初始化LRU缓存
        
        Args:
            capacity: 最大缓存条目数
            default_ttl: 默认过期时间（秒）
        """
        self.capacity = capacity
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, Any] = OrderedDict()
        self.expire_times: dict[str, float] = {}
        self.hits = 0
        self.misses = 0
    
    def _generate_key(self, key: str) -> str:
        """生成缓存键的哈希值"""
        return hashlib.md5(key.encode('utf-8')).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，不存在或已过期返回None
        """
        cache_key = self._generate_key(key)
        
        # 检查是否存在
        if cache_key not in self.cache:
            self.misses += 1
            return None
        
        # 检查是否过期
        if cache_key in self.expire_times:
            if time.time() > self.expire_times[cache_key]:
                # 已过期，删除
                self.delete(key)
                self.misses += 1
                logger.debug(f"缓存过期: {key[:50]}...")
                return None
        
        # 移动到末尾（最近使用）
        self.cache.move_to_end(cache_key)
        self.hits += 1
        logger.debug(f"缓存命中: {key[:50]}...")
        return self.cache[cache_key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None则使用默认值
        """
        cache_key = self._generate_key(key)
        
        # 如果已满，删除最久未使用的
        if len(self.cache) >= self.capacity:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            if oldest_key in self.expire_times:
                del self.expire_times[oldest_key]
            logger.debug(f"缓存已满，淘汰旧数据")
        
        # 设置值和过期时间
        self.cache[cache_key] = value
        self.cache.move_to_end(cache_key)
        
        if ttl is not None:
            self.expire_times[cache_key] = time.time() + ttl
        elif self.default_ttl > 0:
            self.expire_times[cache_key] = time.time() + self.default_ttl
        
        logger.debug(f"缓存设置: {key[:50]}... (TTL: {ttl or self.default_ttl}s)")
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        cache_key = self._generate_key(key)
        if cache_key in self.cache:
            del self.cache[cache_key]
            if cache_key in self.expire_times:
                del self.expire_times[cache_key]
            logger.debug(f"缓存删除: {key[:50]}...")
            return True
        return False
    
    def clear(self) -> None:
        """清空所有缓存"""
        self.cache.clear()
        self.expire_times.clear()
        logger.info("缓存已清空")
    
    def get_stats(self) -> dict:
        """
        获取缓存统计信息
        
        Returns:
            包含命中率、大小等信息的字典
        """
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            'capacity': self.capacity,
            'current_size': len(self.cache),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.2f}%",
            'expired_keys': len([
                k for k, v in self.expire_times.items() 
                if time.time() > v
            ])
        }
    
    def cleanup_expired(self) -> int:
        """
        清理过期的缓存项
        
        Returns:
            清理的数量
        """
        now = time.time()
        expired_keys = [
            k for k, v in self.expire_times.items() 
            if now > v
        ]
        
        for key in expired_keys:
            del self.cache[key]
            del self.expire_times[key]
        
        if expired_keys:
            logger.info(f"清理了 {len(expired_keys)} 个过期缓存项")
        
        return len(expired_keys)


# 全局缓存实例
# 问答结果缓存（较大，TTL较短）
answer_cache = LRUCache(capacity=500, default_ttl=1800)  # 30分钟

# 知识库检索结果缓存（较小，TTL较长）
retrieval_cache = LRUCache(capacity=1000, default_ttl=3600)  # 1小时

# 用户会话缓存
session_cache = LRUCache(capacity=2000, default_ttl=7200)  # 2小时


def init_cache_cleanup_task(interval: int = 300):
    """
    初始化缓存清理定时任务
    
    Args:
        interval: 清理间隔（秒）
    """
    from tornado.ioloop import PeriodicCallback
    
    def cleanup():
        """定期清理过期缓存"""
        answer_cache.cleanup_expired()
        retrieval_cache.cleanup_expired()
        session_cache.cleanup_expired()
        
        # 记录缓存统计
        stats = answer_cache.get_stats()
        logger.info(
            f"📊 缓存统计 - "
            f"问答缓存: {stats['current_size']}/{stats['capacity']} "
            f"(命中率: {stats['hit_rate']})"
        )
    
    cleanup_task = PeriodicCallback(cleanup, interval * 1000)
    cleanup_task.start()
    logger.info(f"✓ 缓存清理任务已启动 (间隔: {interval}秒)")

