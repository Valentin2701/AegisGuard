from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import numpy as np

@dataclass
class NetworkFlow:
    """Core data structure for network flows"""
    source_ip: str
    dest_ip: str
    source_port: int
    dest_port: int
    protocol: str
    pattern: str
    tcp_state: Optional[str] = None
    bytes_sent: int
    packets_sent: int
    qos_class: Optional[str] = None
    dscp: Optional[int] = None
    duration: float
    timestamp: datetime
    label: int  # 0 = normal, 1+ = attack type
    
    def to_features(self) -> np.ndarray:
        """Convert flow to feature vector"""
        # Implementation in feature_extractor.py
        pass
