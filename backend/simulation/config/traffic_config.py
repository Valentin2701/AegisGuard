"""
Traffic configuration and pattern definitions
"""
from typing import Dict, Tuple, List
import random
from .enums import TrafficPattern, Protocol, QoSClass

class TrafficPatternConfig:
    """Configuration for a traffic pattern"""
    
    def __init__(self, pattern: TrafficPattern):
        self.pattern = pattern
        self._config = self._get_config()
    
    def _get_config(self) -> Dict:
        """Get configuration for this pattern"""
        configs = {
            TrafficPattern.WEB_BROWSING: {
                "description": "Web browsing (HTTP/HTTPS traffic)",
                "packet_rate_range": (0.5, 10.0),      # packets/sec
                "avg_packet_size": 1500,               # bytes
                "protocol": Protocol.HTTPS,
                "qos_class": QoSClass.STANDARD,
                "entropy_range": (0.4, 0.7),
                "burstiness": 0.8,                     # 0-1, higher = more bursty
                "typical_duration": (30, 300),         # seconds
                "encryption_probability": 0.7,
            },
            TrafficPattern.VIDEO_STREAMING: {
                "description": "Video streaming (YouTube, Netflix)",
                "packet_rate_range": (20.0, 60.0),
                "avg_packet_size": 1400,
                "protocol": Protocol.UDP,
                "qos_class": QoSClass.VIDEO,
                "entropy_range": (0.7, 0.9),
                "burstiness": 0.2,
                "typical_duration": (300, 3600),
                "encryption_probability": 0.5,
            },
            TrafficPattern.FILE_TRANSFER: {
                "description": "File downloads/uploads",
                "packet_rate_range": (2.0, 20.0),
                "avg_packet_size": 9000,
                "protocol": Protocol.TCP,
                "qos_class": QoSClass.BACKGROUND,
                "entropy_range": (0.8, 0.95),
                "burstiness": 0.3,
                "typical_duration": (10, 600),
                "encryption_probability": 0.3,
            },
            TrafficPattern.EMAIL: {
                "description": "Email traffic (SMTP, IMAP, POP3)",
                "packet_rate_range": (0.05, 0.5),
                "avg_packet_size": 50000,
                "protocol": Protocol.SMTP,
                "qos_class": QoSClass.BACKGROUND,
                "entropy_range": (0.5, 0.8),
                "burstiness": 0.9,
                "typical_duration": (1, 10),
                "encryption_probability": 0.6,
            },
            TrafficPattern.DATABASE: {
                "description": "Database queries/responses",
                "packet_rate_range": (1.0, 50.0),
                "avg_packet_size": 800,
                "protocol": Protocol.TCP,
                "qos_class": QoSClass.CRITICAL,
                "entropy_range": (0.5, 0.8),
                "burstiness": 0.6,
                "typical_duration": (0.1, 5.0),
                "encryption_probability": 0.4,
            },
            TrafficPattern.IOT_SENSOR: {
                "description": "IoT device sensor data",
                "packet_rate_range": (0.1, 1.0),
                "avg_packet_size": 200,
                "protocol": Protocol.UDP,
                "qos_class": QoSClass.BACKGROUND,
                "entropy_range": (0.3, 0.6),
                "burstiness": 0.9,
                "typical_duration": (0.01, 0.1),
                "encryption_probability": 0.2,
            },
            TrafficPattern.VOIP: {
                "description": "Voice over IP calls",
                "packet_rate_range": (20.0, 50.0),
                "avg_packet_size": 200,
                "protocol": Protocol.UDP,
                "qos_class": QoSClass.VOICE,
                "entropy_range": (0.6, 0.8),
                "burstiness": 0.1,
                "typical_duration": (60, 600),
                "encryption_probability": 0.8,
            },
        }
        return configs.get(self.pattern, configs[TrafficPattern.WEB_BROWSING])
    
    @property
    def packet_rate_range(self) -> Tuple[float, float]:
        return self._config["packet_rate_range"]
    
    @property
    def avg_packet_size(self) -> int:
        return self._config["avg_packet_size"]
    
    @property
    def protocol(self) -> Protocol:
        return self._config["protocol"]
    
    @property
    def qos_class(self) -> QoSClass:
        return self._config["qos_class"]
    
    @property
    def entropy_range(self) -> Tuple[float, float]:
        return self._config["entropy_range"]
    
    def generate_packet_rate(self) -> float:
        """Generate random packet rate within range"""
        min_rate, max_rate = self.packet_rate_range
        return random.uniform(min_rate, max_rate)
    
    def generate_packet_size(self) -> int:
        """Generate random packet size"""
        avg = self.avg_packet_size
        # ±20% variation
        return int(random.uniform(avg * 0.8, avg * 1.2))
    
    def generate_entropy(self) -> float:
        """Generate random entropy value"""
        min_ent, max_ent = self.entropy_range
        return random.uniform(min_ent, max_ent)
    
    def should_encrypt(self) -> bool:
        """Determine if traffic should be encrypted"""
        return random.random() < self._config["encryption_probability"]

class TrafficConfig:
    """Main traffic configuration manager"""
    
    # Probability distribution for different traffic patterns
    PATTERN_DISTRIBUTION = {
        TrafficPattern.WEB_BROWSING: 0.40,    # 40% of traffic
        TrafficPattern.VIDEO_STREAMING: 0.25,  # 25%
        TrafficPattern.FILE_TRANSFER: 0.10,    # 10%
        TrafficPattern.EMAIL: 0.05,           # 5%
        TrafficPattern.DATABASE: 0.15,        # 15%
        TrafficPattern.IOT_SENSOR: 0.03,      # 3%
        TrafficPattern.VOIP: 0.02,            # 2%
    }
    
    # Protocol distribution (global internet mix)
    PROTOCOL_DISTRIBUTION = {
        Protocol.TCP: 0.85,      # 85% TCP
        Protocol.UDP: 0.12,      # 12% UDP
        Protocol.ICMP: 0.01,     # 1% ICMP
        Protocol.DNS: 0.02,      # 2% DNS
    }
    
    # Time-of-day patterns (traffic mix changes throughout day)
    TIME_OF_DAY_PATTERNS = {
        "business_hours": {  # 9 AM - 5 PM
            TrafficPattern.WEB_BROWSING: 0.35,
            TrafficPattern.DATABASE: 0.25,
            TrafficPattern.EMAIL: 0.15,
            TrafficPattern.FILE_TRANSFER: 0.15,
            TrafficPattern.VIDEO_STREAMING: 0.05,
            TrafficPattern.VOIP: 0.05,
        },
        "evening": {  # 6 PM - 11 PM
            TrafficPattern.VIDEO_STREAMING: 0.40,
            TrafficPattern.WEB_BROWSING: 0.30,
            TrafficPattern.FILE_TRANSFER: 0.15,
            TrafficPattern.VOIP: 0.10,
            TrafficPattern.EMAIL: 0.05,
        },
        "night": {  # 11 PM - 6 AM
            TrafficPattern.FILE_TRANSFER: 0.40,  # Backups
            TrafficPattern.IOT_SENSOR: 0.30,
            TrafficPattern.WEB_BROWSING: 0.20,
            TrafficPattern.EMAIL: 0.10,
        },
    }
    
    # Common service ports
    SERVICE_PORTS = {
        "http": 80,
        "https": 443,
        "ssh": 22,
        "ftp": 21,
        "smtp": 25,
        "smtps": 465,
        "dns": 53,
        "dhcp_server": 67,
        "dhcp_client": 68,
        "pop3": 110,
        "pop3s": 995,
        "imap": 143,
        "imaps": 993,
        "mysql": 3306,
        "postgresql": 5432,
        "mongodb": 27017,
        "redis": 6379,
        "rdp": 3389,
        "vnc": 5900,
        "snmp": 161,
        "ntp": 123,
        "ldap": 389,
        "ldaps": 636,
    }
    
    @classmethod
    def get_pattern_config(cls, pattern: TrafficPattern) -> TrafficPatternConfig:
        """Get configuration for a specific pattern"""
        return TrafficPatternConfig(pattern)
    
    @classmethod
    def get_random_pattern(cls, time_of_day: str = "business_hours") -> TrafficPattern:
        """Get random pattern based on time of day"""
        distribution = cls.TIME_OF_DAY_PATTERNS.get(
            time_of_day, 
            cls.PATTERN_DISTRIBUTION
        )
        patterns = list(distribution.keys())
        weights = list(distribution.values())
        return random.choices(patterns, weights=weights, k=1)[0]
    
    @classmethod
    def get_service_port(cls, service_name: str) -> int:
        """Get port number for a service"""
        return cls.SERVICE_PORTS.get(service_name.lower(), 80)  # Default to HTTP
    
    @classmethod
    def find_service_by_port(cls, port: int) -> str:
        """Find service name by port number"""
        for service, service_port in cls.SERVICE_PORTS.items():
            if service_port == port:
                return service
        return "unknown"
    
    @classmethod
    def get_encryption_strength(cls, protocol: Protocol) -> int:
        """Get encryption strength for protocol (0-100)"""
        strength_map = {
            Protocol.HTTPS: 90,
            Protocol.SSH: 95,
            Protocol.TLS: 92,
            Protocol.IPSEC: 98,
            Protocol.FTPS: 85,
            Protocol.SMTPS: 88,
            Protocol.IMAPS: 88,
            Protocol.POP3S: 88,
            Protocol.LDAPS: 85,
        }
        return strength_map.get(protocol, 0)