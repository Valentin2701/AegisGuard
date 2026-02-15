import json
from datetime import datetime, timedelta
import threading
import pickle
from typing import Optional, List, Dict, Any

from .redis_client import RedisClient

class RedisStateManager:
    """Manages all simulation state in Redis"""
    
    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
        self._lock = threading.Lock()
        
        # Initialize counters if not exists
        self._init_counters()
    
    def _init_counters(self):
        """Initialize atomic counters"""
        pipeline = self.redis.pipeline()
        
        # Attack counter
        if not self.redis.exists('counters:attack'):
            pipeline.set('counters:attack', 0)
        
        # Honeypot counter
        if not self.redis.exists('counters:honeypot'):
            pipeline.set('counters:honeypot', 0)
        
        # Agent counter
        if not self.redis.exists('counters:agent'):
            pipeline.set('counters:agent', 4)  # Start with 4 agents
        
        pipeline.execute()
