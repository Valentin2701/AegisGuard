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

# ==================== TRAFFIC ENUMS ====================

class TrafficPattern(Enum):
    """Types of traffic patterns with properties"""
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
    
    @property
    def protocol(self):
        """Default protocol for this pattern"""
        protocols = {
            self.WEB_BROWSING: "HTTPS",
            self.VIDEO_STREAMING: "UDP",
            self.FILE_TRANSFER: "TCP",
            self.EMAIL: "SMTP",
            self.DATABASE: "TCP",
            self.IOT_SENSOR: "UDP",
            self.VOIP: "UDP",
            self.VIDEO_CONFERENCING: "UDP",
            self.BACKUP: "TCP",
            self.GAMING: "UDP",
            self.CLOUD_SYNC: "HTTPS",
            self.API_CALLS: "HTTPS",
        }
        return protocols.get(self, "TCP")
    
    @property
    def packet_rate(self):
        """Packets per second"""
        rates = {
            self.WEB_BROWSING: 7.5,
            self.VIDEO_STREAMING: 40.0,
            self.FILE_TRANSFER: 11.0,
            self.EMAIL: 0.25,
            self.DATABASE: 25.0,
            self.IOT_SENSOR: 0.5,
            self.VOIP: 35.0,
            self.VIDEO_CONFERENCING: 65.0,
            self.BACKUP: 10.0,
            self.GAMING: 25.0,
            self.CLOUD_SYNC: 3.0,
            self.API_CALLS: 2.5,
        }
        return rates.get(self, 5.0)
    
    @property
    def avg_packet_size(self):
        """Average packet size in bytes"""
        sizes = {
            self.WEB_BROWSING: 1500,
            self.VIDEO_STREAMING: 1400,
            self.FILE_TRANSFER: 9000,
            self.EMAIL: 50000,
            self.DATABASE: 800,
            self.IOT_SENSOR: 200,
            self.VOIP: 200,
            self.VIDEO_CONFERENCING: 1200,
            self.BACKUP: 9000,
            self.GAMING: 600,
            self.CLOUD_SYNC: 2000,
            self.API_CALLS: 1200,
        }
        return sizes.get(self, 1000)
    
    @property
    def qos_class(self):
        """Quality of Service class for this pattern"""
        from .enums import QoSClass
        qos_map = {
            self.WEB_BROWSING: QoSClass.STANDARD,
            self.VIDEO_STREAMING: QoSClass.VIDEO,
            self.FILE_TRANSFER: QoSClass.BACKGROUND,
            self.EMAIL: QoSClass.BACKGROUND,
            self.DATABASE: QoSClass.CRITICAL,
            self.IOT_SENSOR: QoSClass.BACKGROUND,
            self.VOIP: QoSClass.VOICE,
            self.VIDEO_CONFERENCING: QoSClass.VIDEO,
            self.BACKUP: QoSClass.BACKGROUND,
            self.GAMING: QoSClass.STANDARD,
            self.CLOUD_SYNC: QoSClass.STANDARD,
            self.API_CALLS: QoSClass.STANDARD,
        }
        return qos_map.get(self, QoSClass.BEST_EFFORT)
    
    @property
    def entropy_range(self):
        """Payload entropy range (0-1)"""
        ranges = {
            self.WEB_BROWSING: (0.4, 0.7),
            self.VIDEO_STREAMING: (0.7, 0.9),
            self.FILE_TRANSFER: (0.8, 0.95),
            self.EMAIL: (0.5, 0.8),
            self.DATABASE: (0.5, 0.8),
            self.IOT_SENSOR: (0.3, 0.6),
            self.VOIP: (0.6, 0.8),
            self.VIDEO_CONFERENCING: (0.7, 0.9),
            self.BACKUP: (0.8, 0.95),
            self.GAMING: (0.6, 0.8),
            self.CLOUD_SYNC: (0.7, 0.9),
            self.API_CALLS: (0.5, 0.8),
        }
        return ranges.get(self, (0.5, 0.7))
    
    @property
    def description(self):
        """Human-readable description"""
        descriptions = {
            self.WEB_BROWSING: "Web browsing (HTTP/HTTPS traffic)",
            self.VIDEO_STREAMING: "Video streaming (YouTube, Netflix)",
            self.FILE_TRANSFER: "File downloads/uploads",
            self.EMAIL: "Email traffic (SMTP, IMAP, POP3)",
            self.DATABASE: "Database queries/responses",
            self.IOT_SENSOR: "IoT device sensor data",
            self.VOIP: "Voice over IP calls",
            self.VIDEO_CONFERENCING: "Video conferencing",
            self.BACKUP: "Data backup transfers",
            self.GAMING: "Online gaming traffic",
            self.CLOUD_SYNC: "Cloud storage synchronization",
            self.API_CALLS: "API requests/responses",
        }
        return descriptions.get(self, "Generic network traffic")

# ==================== ATTACK ENUMS ====================
class AttackType(Enum):
    """Types of cyber attacks"""
    PORT_SCAN = "port_scan"
    DDOS = "ddos"
    MALWARE_SPREAD = "malware_spread"
    ARP_SPOOFING = "arp_spoofing"
    SQL_INJECTION = "sql_injection"
    BRUTE_FORCE = "brute_force"
    XSS = "xss"
    CSRF = "csrf"
    ZERO_DAY = "zero_day"

class AttackSeverity(Enum):
    """Attack severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"