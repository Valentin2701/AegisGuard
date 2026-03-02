from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import numpy as np

@dataclass
class NetworkFlow:
    """Core data structure for network flows"""
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    pattern: str
    bytes_sent: int
    packets_sent: int
    duration: float
    timestamp: datetime
    label: int  # 0 = normal, 1+ = attack type
    id: str = None
    tcp_state: str = None
    qos_class: str = None
    dscp: int = None
    
    def to_features(self) -> np.ndarray:
        """Convert flow to feature vector"""
        # Implementation in feature_extractor.py
        pass
