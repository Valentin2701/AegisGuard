__version__ = "0.2.0"
__author__ = "Valentin2701"

# Import from local config subpackage
from .config.enums import (
    NodeType, OperatingSystem, Protocol,
    PacketType, PacketStatus, Direction, QoSClass, 
    TrafficPattern, AttackType, AttackSeverity,
)

from .config.network_config import NetworkConfig
from .config.traffic_config import TrafficConfig
from .config.attack_config import AttackConfig

# Import simulation modules
from .network_node import NetworkNode
from .network_edge import NetworkEdge
from .network_graph import NetworkGraph
from .packet import Packet
from .traffic_generator import TrafficGenerator
from .attack_generator import AttackGenerator

# Export everything
__all__ = [
    # Configurations
    "NetworkConfig",
    "TrafficConfig",
    "AttackConfig",

    # Core classes
    "NetworkNode",
    "NetworkEdge",
    "NetworkGraph", 
    "Packet",
    "TrafficGenerator",
    "AttackGenerator",
    
    # Enums from config
    "NodeType",
    "OperatingSystem", 
    "Protocol",
    "PacketType",
    "PacketStatus",
    "Direction",
    "QoSClass",
    "TrafficPattern",
    "AttackType",
    "AttackSeverity",
]