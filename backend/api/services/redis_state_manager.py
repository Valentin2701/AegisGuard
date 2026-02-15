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
    
    # ============ Network Management ============
    
    def save_network_graph(self, network_graph):
        """Save network graph to Redis"""
        network_pickle = pickle.dumps(network_graph)
        self.redis.set('network:graph', network_pickle)
        self.redis.expire('network:graph', timedelta(hours=24))
    
    def load_network_graph(self):
        """Load network graph from Redis"""
        network_pickle = self.redis.get('network:graph')
        if network_pickle:
            return pickle.loads(network_pickle)
        return None
    
    def add_node(self, node_id: str, node_data: Dict):
        """Add a node to the network"""
        key = f"node:{node_id}"
        
        # Store node as hash
        pipeline = self.redis.pipeline()
        for field, value in node_data.items():
            pipeline.hset(key, field, value)
        
        # Add to all nodes set
        pipeline.sadd('nodes:all', node_id)
        
        # Add to status set
        status = node_data.get('status', 'healthy')
        pipeline.sadd(f'nodes:{status}', node_id)
        
        pipeline.execute()
        
        # Publish update
        self.redis.publish('network', {
            'event': 'node_added',
            'node_id': node_id,
            'timestamp': datetime.now().isoformat()
        })
    
    def update_node_status(self, node_id: str, new_status: str):
        """Update node status"""
        # Get current status
        current_status = self.redis.hget(f"node:{node_id}", 'status')
        
        if current_status and current_status != new_status:
            pipeline = self.redis.pipeline()
            
            # Remove from old status set
            pipeline.srem(f'nodes:{current_status}', node_id)
            
            # Add to new status set
            pipeline.sadd(f'nodes:{new_status}', node_id)
            
            # Update node hash
            pipeline.hset(f"node:{node_id}", 'status', new_status)
            pipeline.hset(f"node:{node_id}", 'updated_at', datetime.now().isoformat())
            
            pipeline.execute()
            
            # Publish update
            self.redis.publish('network', {
                'event': 'node_status_changed',
                'node_id': node_id,
                'old_status': current_status,
                'new_status': new_status,
                'timestamp': datetime.now().isoformat()
            })
    
    def get_all_nodes(self) -> List[Dict]:
        """Get all network nodes"""
        node_ids = self.redis.smembers('nodes:all')
        nodes = []
        
        for node_id in node_ids:
            node_data = self.redis.hgetall(f"node:{node_id}")
            if node_data:
                node_data['id'] = node_id
                nodes.append(node_data)
        
        return nodes
    
    def get_nodes_by_status(self, status: str) -> List[Dict]:
        """Get nodes by status"""
        node_ids = self.redis.smembers(f'nodes:{status}')
        nodes = []
        
        for node_id in node_ids:
            node_data = self.redis.hgetall(f"node:{node_id}")
            if node_data:
                node_data['id'] = node_id
                nodes.append(node_data)
        
        return nodes
    
