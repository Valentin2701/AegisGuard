__version__ = "0.2.0"
__author__ = "Valentin2701"

# Import from local config subpackage
from .config.enums import (
    NodeType, OperatingSystem, Protocol,
    PacketType, PacketStatus, Direction, QoSClass, 
    TrafficPattern
)

from .config.network_config import NetworkConfig
#from .config.traffic_config import TrafficConfig

# Import simulation modules
from .network_node import NetworkNode
from .network_edge import NetworkEdge
from .network_graph import NetworkGraph
from .packet import Packet

# Export everything
__all__ = [
    # Configurations
    "NetworkConfig",

    # Core classes
    "NetworkNode",
    "NetworkEdge",
    "NetworkGraph", 
    "Packet",
    
    # Enums from config
    "NodeType",
    "OperatingSystem", 
    "Protocol",
    "PacketType",
    "PacketStatus",
    "Direction",
    "QoSClass",
    "TrafficPattern",
]