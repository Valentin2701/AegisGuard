from enum import Enum
# -------- Network Enums --------

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

class Protocol(Enum):
    TCP = "tcp"
    UDP = "udp"
    ICMP = "icmp"
    HTTP = "http"
    HTTPS = "https"
    SSH = "ssh"
    FTP = "ftp"
    DNS = "dns"
    DHCP = "dhcp"
    ARP = "arp"
    BGP = "bgp"
    OSPF = "ospf"
    TLS = "tls"
    IPSEC = "ipsec"
    SMTP = "smtp"
    POP3 = "pop3"
    IMAP = "imap"

    def __init__(self, protocol_name):
        self.protocol_name = protocol_name
    
    @property
    def is_encrypted(self):
        return self in [Protocol.HTTPS, Protocol.SSH, 
                       Protocol.TLS, Protocol.IPSEC]
    
# --------- Packet Enums --------

class PacketType(Enum):
    DATA = "data"
    CONTROL = "control"
    MANAGEMENT = "management"
    ATTACK = "attack" 
    RESPONSE = "response"
    ROUTING = "routing"  # OSPF, BGP, etc.

class PacketStatus(Enum):
    """Packet transmission status"""
    CREATED = "created"
    SENT = "sent"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    DROPPED = "dropped"
    CORRUPTED = "corrupted"
    QUEUED = "queued"  # Waiting in buffer

class Direction(Enum):
    """Packet direction"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    INTERNAL = "internal"

class QoSClass(Enum):
    """Quality of Service classes"""
    BEST_EFFORT = "best_effort"      # Default internet traffic
    BACKGROUND = "background"        # Bulk transfers, backups
    STANDARD = "standard"           # Normal business traffic
    VIDEO = "video"                 # Streaming media
    VOICE = "voice"                 # VoIP, real-time audio
    CRITICAL = "critical"           # Emergency, control systems
    NETWORK_CONTROL = "network_control"  # Routing protocols

class TrafficPattern(Enum):
    """Types of traffic patterns"""
    WEB_BROWSING = "web_browsing"
    VIDEO_STREAMING = "video_streaming"
    FILE_TRANSFER = "file_transfer"
    EMAIL = "email"
    DATABASE = "database"
    IOT_SENSOR = "iot_sensor"
    VOIP = "voip"
    VIDEO_CONFERENCING = "video_conferencing"
    BACKUP = "backup"
    GAMING = "gaming"
    CLOUD_SYNC = "cloud_sync"
    API_CALLS = "api_calls"