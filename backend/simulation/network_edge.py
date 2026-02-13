from enum import Enum
from dataclasses import dataclass
from typing import Optional
from .config.enums import Protocol

@dataclass
class NetworkEdge:
    id: str
    source_id: str
    target_id: str
    
    # Connection properties
    bandwidth: float  # Mbps
    latency: float    # ms
    supported_protocols: list[Protocol]
    current_protocol: Optional[Protocol] = None
    
    # Security properties
    encryption_level: int = 0  # 0-100
    is_monitored: bool = False
    
    # Traffic metrics
    traffic_volume: float = 0.0  # Mbps currently used
    packet_count: int = 0
    error_rate: float = 0.0  # 0-1
    
    def __post_init__(self):
        if self.current_protocol is None and self.supported_protocols:
            self.current_protocol = self.supported_protocols[0]
    
    def get_security_score(self) -> float:
        """Calculate security score of this connection"""
        base_score = self.encryption_level / 100.0
        
        # Protocol security modifiers
        protocol_scores = {
            Protocol.HTTP: 0.3,
            Protocol.HTTPS: 0.8,
            Protocol.TCP: 0.5,
            Protocol.UDP: 0.4,
            Protocol.TLS: 0.9,
            Protocol.IPSEC: 0.95,
            Protocol.SSH: 0.85,
            Protocol.FTP: 0.2
        }
        
        protocol_score = protocol_scores.get(self.current_protocol, 0.5)
        
        return (base_score + protocol_score) / 2
    
    def to_dict(self):
        return {
        "id": self.id,
        "source": self.source_id,
        "target": self.target_id,
        "bandwidth": self.bandwidth,
        "latency": self.latency,
        "supported_protocols": [p.value for p in self.supported_protocols],
        "current_protocol": self.current_protocol.value if self.current_protocol else None,
        "encryption_level": self.encryption_level,
        "is_monitored": self.is_monitored,
        "traffic_volume": self.traffic_volume,
        "packet_count": self.packet_count,
        "error_rate": self.error_rate,
        "security_score": self.get_security_score()
    }