import redis
from typing import Optional, Any

class RedisClient:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True
        )
    
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """设置键值对，可选设置过期时间"""
        result = self.client.set(key, value)
        if expire:
            self.client.expire(key, expire)
        return result
    
    def get(self, key: str) -> Optional[str]:
        """获取键值"""
        return self.client.get(key)
    
    def delete(self, key: str) -> int:
        """删除键"""
        return self.client.delete(key)
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return self.client.exists(key) > 0
    
    def hset(self, name: str, key: str, value: Any) -> int:
        """设置哈希表字段"""
        return self.client.hset(name, key, value)
    
    def hget(self, name: str, key: str) -> Optional[str]:
        """获取哈希表字段"""
        return self.client.hget(name, key)
    
    def hgetall(self, name: str) -> dict:
        """获取哈希表所有字段"""
        return self.client.hgetall(name)
    
    def hdel(self, name: str, *keys) -> int:
        """删除哈希表字段"""
        return self.client.hdel(name, *keys)

# 创建全局Redis客户端实例
redis_client = RedisClient()