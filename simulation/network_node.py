from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional

class NodeType(Enum):
    CLIENT = "client"
    SERVER = "server"
    ROUTER = "router"
    SWITCH = "switch"
    FIREWALL = "firewall"
    HONEYPOT = "honeypot"

class OperatingSystem(Enum):
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    IOS = "ios"
    ANDROID = "android"
    CUSTOM = "custom"

@dataclass
class NetworkNode:
    id: str
    name: str
    node_type: NodeType
    os: OperatingSystem
    ip_address: str
    mac_address: str
    
    # Security properties
    security_level: int = 50  # 0-100
    is_compromised: bool = False
    is_quarantined: bool = False
    
    # Services running on this node
    services: List[str] = None  # e.g., ["http", "ssh", "ftp"]
    
    # Performance metrics
    cpu_usage: float = 0.0  # 0-100%
    memory_usage: float = 0.0  # 0-100%
    bandwidth_used: float = 0.0  # Mbps
    
    # Value for scoring
    value_score: int = 1  # 1-10, importance
    
    def __post_init__(self):
        if self.services is None:
            self.services = []
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.node_type.value,
            "os": self.os.value,
            "ip": self.ip_address,
            "mac": self.mac_address,
            "security_level": self.security_level,
            "is_compromised": self.is_compromised,
            "is_quarantined": self.is_quarantined,
            "services": self.services,
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "bandwidth_used": self.bandwidth_used,
            "value_score": self.value_score
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data["id"],
            name=data["name"],
            node_type=NodeType(data["type"]),
            os=OperatingSystem(data["os"]),
            ip_address=data["ip"],
            mac_address=data["mac"],
            security_level=data["security_level"],
            is_compromised=data["is_compromised"],
            is_quarantined=data["is_quarantined"],
            services=data["services"],
            cpu_usage=data["cpu_usage"],
            memory_usage=data["memory_usage"],
            bandwidth_used=data["bandwidth_used"],
            value_score=data["value_score"]
        )