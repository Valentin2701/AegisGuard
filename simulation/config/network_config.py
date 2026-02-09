from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import random
from .enums import NodeType, OperatingSystem, Protocol

@dataclass
class NodeTemplate:
    """Template for creating nodes of specific types"""
    node_type: NodeType
    os: OperatingSystem
    default_services: List[str]
    security_range: Tuple[int, int]  # min, max security level
    value_range: Tuple[int, int]     # min, max importance value
    typical_bandwidth: int  # Mbps
    
    def generate_security_level(self) -> int:
        """Generate random security level within range"""
        return random.randint(*self.security_range)
    
    def generate_value_score(self) -> int:
        """Generate random value score within range"""
        return random.randint(*self.value_range)

class NetworkConfig:
    """Network configuration presets"""
    
    # Node templates for different node types
    NODE_TEMPLATES = {
        NodeType.CLIENT: NodeTemplate(
            node_type=NodeType.CLIENT,
            os=OperatingSystem.WINDOWS,
            default_services=["browser", "office", "email", "vpn"],
            security_range=(40, 70),
            value_range=(3, 6),
            typical_bandwidth=100  # 100 Mbps
        ),
        
        NodeType.SERVER: NodeTemplate(
            node_type=NodeType.SERVER,
            os=OperatingSystem.LINUX,
            default_services=["http", "ssh", "database", "backup"],
            security_range=(60, 85),
            value_range=(7, 10),
            typical_bandwidth=1000  # 1 Gbps
        ),
        
        NodeType.ROUTER: NodeTemplate(
            node_type=NodeType.ROUTER,
            os=OperatingSystem.CUSTOM,
            default_services=["routing", "nat", "dhcp", "firewall"],
            security_range=(70, 90),
            value_range=(8, 10),
            typical_bandwidth=10000  # 10 Gbps
        ),
        
        NodeType.FIREWALL: NodeTemplate(
            node_type=NodeType.FIREWALL,
            os=OperatingSystem.LINUX,
            default_services=["firewall", "ids", "vpn", "proxy"],
            security_range=(80, 95),
            value_range=(9, 10),
            typical_bandwidth=1000  # 1 Gbps
        ),
        
        NodeType.SWITCH: NodeTemplate(
            node_type=NodeType.SWITCH,
            os=OperatingSystem.CUSTOM,
            default_services=["switching", "vlan", "stp"],
            security_range=(60, 80),
            value_range=(5, 7),
            typical_bandwidth=10000  # 10 Gbps
        ),
        
        NodeType.HONEYPOT: NodeTemplate(
            node_type=NodeType.HONEYPOT,
            os=OperatingSystem.LINUX,
            default_services=["http", "ssh", "ftp", "telnet", "smb"],
            security_range=(30, 50),  # Intentionally weak
            value_range=(1, 3),       # Low apparent value
            typical_bandwidth=100     # 100 Mbps
        ),
    }
    
    # Network topology presets
    TOPOLOGY_PRESETS = {
        "small_office": {
            "description": "Small business network (10-20 nodes)",
            "node_counts": {
                NodeType.CLIENT: 8,
                NodeType.SERVER: 3,
                NodeType.ROUTER: 1,
                NodeType.SWITCH: 2,
                NodeType.FIREWALL: 1,
            },
            "ip_range": "192.168.1.0/24",
            "dns_server": "192.168.1.1",
            "gateway": "192.168.1.1",
        },
        
        "university_campus": {
            "description": "University campus network (100+ nodes)",
            "node_counts": {
                NodeType.CLIENT: 80,
                NodeType.SERVER: 15,
                NodeType.ROUTER: 5,
                NodeType.SWITCH: 20,
                NodeType.FIREWALL: 3,
            },
            "ip_range": "10.0.0.0/16",
            "dns_server": "10.0.0.1",
            "gateway": "10.0.0.1",
        },
        
        "data_center": {
            "description": "Cloud data center (50+ servers)",
            "node_counts": {
                NodeType.SERVER: 40,
                NodeType.SWITCH: 8,
                NodeType.ROUTER: 2,
                NodeType.FIREWALL: 2,
            },
            "ip_range": "172.16.0.0/12",
            "dns_server": "172.16.0.1",
            "gateway": "172.16.0.1",
        },
        
        "iot_network": {
            "description": "IoT/Smart Home network",
            "node_counts": {
                NodeType.CLIENT: 20,
                NodeType.SERVER: 2,
                NodeType.ROUTER: 1,
                NodeType.SWITCH: 1,
                NodeType.FIREWALL: 1,
            },
            "ip_range": "10.10.0.0/24",
            "dns_server": "10.10.0.1",
            "gateway": "10.10.0.1",
        },
    }
    
    # Protocol configurations
    PROTOCOL_CONFIGS = {
        Protocol.TCP: {
            "default_ports": [80, 443, 22, 21, 25, 110, 143, 3389],
            "requires_handshake": True,
            "reliable": True,
            "connection_oriented": True,
        },
        
        Protocol.UDP: {
            "default_ports": [53, 67, 68, 123, 161, 500, 1701],
            "requires_handshake": False,
            "reliable": False,
            "connection_oriented": False,
        },
        
        Protocol.HTTP: {
            "default_ports": [80, 8080, 8000],
            "is_encrypted": False,
            "typical_payload_size": (500, 1500),  # bytes
        },
        
        Protocol.HTTPS: {
            "default_ports": [443, 8443],
            "is_encrypted": True,
            "encryption_strength": 85,
            "typical_payload_size": (600, 1600),
        },
        
        Protocol.SSH: {
            "default_ports": [22],
            "is_encrypted": True,
            "encryption_strength": 90,
            "typical_payload_size": (100, 1000),
        },
    }
    
    @classmethod
    def get_node_template(cls, node_type: NodeType) -> Optional[NodeTemplate]:
        """Get template for a node type"""
        return cls.NODE_TEMPLATES.get(node_type)
    
    @classmethod
    def get_topology_preset(cls, preset_name: str) -> Optional[Dict]:
        """Get topology configuration preset"""
        return cls.TOPOLOGY_PRESETS.get(preset_name)
    
    @classmethod
    def get_protocol_config(cls, protocol: Protocol) -> Optional[Dict]:
        """Get configuration for a protocol"""
        return cls.PROTOCOL_CONFIGS.get(protocol)