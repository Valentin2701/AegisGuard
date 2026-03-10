from collections import deque
import threading
import time
from typing import List

from ..interface import NetworkFlow

class TemporalWindow:
    """
    Maintains sliding window of flows and builds temporal graphs
    """
    
    def __init__(self, window_size: int = 60, stride: int = 10):
        self.window_size = window_size  # seconds
        self.stride = stride  # seconds
        self.buffer = deque()
        self.lock = threading.Lock()
        
    def add_flows(self, flows: List[NetworkFlow]):
        """Add new flows to buffer"""
        with self.lock:
            self.buffer.extend(flows)
            
            # Remove old flows
            current_time = time.time()
            while self.buffer and current_time - self.buffer[0].timestamp > self.window_size:
                self.buffer.popleft()
    
    def get_window(self) -> List[NetworkFlow]:
        """Get current window of flows"""
        with self.lock:
            return list(self.buffer)