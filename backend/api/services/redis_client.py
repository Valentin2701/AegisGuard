import redis
import json
import pickle
from datetime import datetime, timedelta
from typing import Any, Optional, List, Dict
import logging

class RedisClient:
    """Redis client wrapper for Aegis Guard"""
    
    def __init__(self, host='localhost', port=6379, db=0, password=None, prefix='aegis'):
        self.prefix = prefix
        
        # Connection pools for better performance
        self.redis_pool = redis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=False,
            max_connections=10
        )
        
        self.json_pool = redis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,
            max_connections=10
        )
        
        # Clients for different purposes
        self.redis = redis.Redis(connection_pool=self.redis_pool)
        self.json_redis = redis.Redis(connection_pool=self.json_pool)
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def _key(self, *parts):
        """Build Redis key with prefix"""
        return f"{self.prefix}:{':'.join(str(p) for p in parts)}"
    
    def ping(self) -> bool:
        """Test Redis connection"""
        try:
            return self.redis.ping()
        except redis.ConnectionError:
            self.logger.error("Redis connection failed")
            return False
    
    # ============ String Operations ============
    def set(self, key: str, value: Any, expire: int = None) -> bool:
        """Set a string value"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            result = self.redis.set(key, str(value))
            if expire:
                self.redis.expire(key, expire)
            return result
        except Exception as e:
            self.logger.error(f"Redis set error: {e}")
            return False
    
    def get(self, key: str, default=None) -> Any:
        """Get a string value"""
        try:
            value = self.redis.get(key)
            if value:
                # Try to parse as JSON
                try:
                    return json.loads(value)
                except:
                    return value.decode('utf-8') if isinstance(value, bytes) else value
            return default
        except Exception as e:
            self.logger.error(f"Redis get error: {e}")
            return default
    
    # ============ Hash Operations ============
    def hset(self, key: str, field: str, value: Any) -> bool:
        """Set hash field"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            return self.redis.hset(key, field, str(value))
        except Exception as e:
            self.logger.error(f"Redis hset error: {e}")
            return False
    
    def hget(self, key: str, field: str, default=None) -> Any:
        """Get hash field"""
        try:
            value = self.redis.hget(key, field)
            if value:
                try:
                    return json.loads(value)
                except:
                    return value.decode('utf-8') if isinstance(value, bytes) else value
            return default
        except Exception as e:
            self.logger.error(f"Redis hget error: {e}")
            return default
    
    def hgetall(self, key: str) -> Dict:
        """Get all hash fields"""
        try:
            result = self.redis.hgetall(key)
            decoded = {}
            for k, v in result.items():
                k = k.decode('utf-8')
                try:
                    decoded[k] = json.loads(v)
                except:
                    decoded[k] = v.decode('utf-8') if isinstance(v, bytes) else v
            return decoded
        except Exception as e:
            self.logger.error(f"Redis hgetall error: {e}")
            return {}
    
    # ============ List Operations ============
    def lpush(self, key: str, *values) -> int:
        """Push values to list head"""
        try:
            json_values = [json.dumps(v) if isinstance(v, (dict, list)) else str(v) for v in values]
            return self.redis.lpush(key, *json_values)
        except Exception as e:
            self.logger.error(f"Redis lpush error: {e}")
            return 0
    
    def lrange(self, key: str, start: int, end: int) -> List:
        """Get list range"""
        try:
            values = self.redis.lrange(key, start, end)
            result = []
            for v in values:
                try:
                    result.append(json.loads(v))
                except:
                    result.append(v.decode('utf-8') if isinstance(v, bytes) else v)
            return result
        except Exception as e:
            self.logger.error(f"Redis lrange error: {e}")
            return []
    
    def ltrim(self, key: str, start: int, end: int) -> bool:
        """Trim list to range"""
        try:
            return self.redis.ltrim(key, start, end)
        except Exception as e:
            self.logger.error(f"Redis ltrim error: {e}")
            return False
    
    # ============ Set Operations ============
    def sadd(self, key: str, *members) -> int:
        """Add members to set"""
        try:
            return self.redis.sadd(key, *members)
        except Exception as e:
            self.logger.error(f"Redis sadd error: {e}")
            return 0
    
    def srem(self, key: str, *members) -> int:
        """Remove members from set"""
        try:
            return self.redis.srem(key, *members)
        except Exception as e:
            self.logger.error(f"Redis srem error: {e}")
            return 0
    
    def smembers(self, key: str) -> List:
        """Get all set members"""
        try:
            members = self.redis.smembers(key)
            return [m.decode('utf-8') if isinstance(m, bytes) else m for m in members]
        except Exception as e:
            self.logger.error(f"Redis smembers error: {e}")
            return []
    
    # ============ Sorted Set Operations ============
    def zadd(self, key: str, mapping: Dict) -> int:
        """Add to sorted set with scores"""
        try:
            return self.redis.zadd(key, mapping)
        except Exception as e:
            self.logger.error(f"Redis zadd error: {e}")
            return 0
    
    def zrange(self, key: str, start: int, end: int, withscores: bool = False) -> List:
        """Get range from sorted set"""
        try:
            return self.redis.zrange(key, start, end, withscores=withscores)
        except Exception as e:
            self.logger.error(f"Redis zrange error: {e}")
            return []
    
    # ============ Pub/Sub ============
    def publish(self, channel: str, message: Any) -> int:
        """Publish message to channel"""
        try:
            if isinstance(message, (dict, list)):
                message = json.dumps(message)
            return self.redis.publish(self._key('channel', channel), message)
        except Exception as e:
            self.logger.error(f"Redis publish error: {e}")
            return 0
    
    def pubsub(self):
        """Get pubsub object"""
        return self.redis.pubsub()
    
    # ============ Key Operations ============
    def delete(self, *keys) -> int:
        """Delete keys"""
        try:
            return self.redis.delete(*keys)
        except Exception as e:
            self.logger.error(f"Redis delete error: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return self.redis.exists(key) > 0
        except Exception as e:
            self.logger.error(f"Redis exists error: {e}")
            return False
    
    def expire(self, key: str, seconds: int) -> bool:
        """Set key expiration"""
        try:
            return self.redis.expire(key, seconds)
        except Exception as e:
            self.logger.error(f"Redis expire error: {e}")
            return False
    
    # ============ Pipeline/Transaction ============
    def pipeline(self):
        """Get Redis pipeline"""
        return self.redis.pipeline()
    
    # ============ Flush/Cleanup ============
    def flush_all(self) -> bool:
        """Flush all Redis data (use with caution!)"""
        try:
            self.redis.flushdb()
            return True
        except Exception as e:
            self.logger.error(f"Redis flush error: {e}")
            return False