"""
Attack configuration for NetSentinel AI
"""
from typing import Dict, List, Tuple, Any
import random
from .enums import AttackType, Protocol, AttackSeverity

class AttackConfig:
    """Configuration for cyber attacks"""
    
    # Attack severity mapping
    ATTACK_SEVERITY = {
        AttackType.PORT_SCAN: AttackSeverity.LOW,
        AttackType.VULNERABILITY_SCAN: AttackSeverity.LOW,
        AttackType.OS_FINGERPRINTING: AttackSeverity.LOW,
        AttackType.ARP_SPOOFING: AttackSeverity.MEDIUM,
        AttackType.DNS_SPOOFING: AttackSeverity.MEDIUM,
        AttackType.BRUTE_FORCE: AttackSeverity.MEDIUM,
        AttackType.SQL_INJECTION: AttackSeverity.MEDIUM,
        AttackType.XSS: AttackSeverity.MEDIUM,
        AttackType.CSRF: AttackSeverity.MEDIUM,
        AttackType.MALWARE_SPREAD: AttackSeverity.HIGH,
        AttackType.RANSOMWARE: AttackSeverity.HIGH,
        AttackType.TROJAN: AttackSeverity.HIGH,
        AttackType.WORM: AttackSeverity.HIGH,
        AttackType.DDOS: AttackSeverity.HIGH,
        AttackType.DOS: AttackSeverity.HIGH,
        AttackType.HTTP_FLOOD: AttackSeverity.HIGH,
        AttackType.SYN_FLOOD: AttackSeverity.HIGH,
        AttackType.UDP_FLOOD: AttackSeverity.HIGH,
        AttackType.ICMP_FLOOD: AttackSeverity.HIGH,
        AttackType.MAN_IN_THE_MIDDLE: AttackSeverity.CRITICAL,
        AttackType.ZERO_DAY: AttackSeverity.CRITICAL,
        AttackType.APT: AttackSeverity.CRITICAL,
        AttackType.LATERAL_MOVEMENT: AttackSeverity.CRITICAL,
        AttackType.DATA_EXFILTRATION: AttackSeverity.CRITICAL,
    }
    
    # Attack probabilities (per second in a network)
    ATTACK_PROBABILITIES = {
        AttackType.PORT_SCAN: 0.02,           # 2% chance per second
        AttackType.VULNERABILITY_SCAN: 0.01,   # 1%
        AttackType.BRUTE_FORCE: 0.008,        # 0.8%
        AttackType.DDOS: 0.005,               # 0.5%
        AttackType.MALWARE_SPREAD: 0.01,      # 1%
        AttackType.SQL_INJECTION: 0.003,      # 0.3%
        AttackType.XSS: 0.002,                # 0.2%
        AttackType.SYN_FLOOD: 0.004,          # 0.4%
        AttackType.ARP_SPOOFING: 0.001,       # 0.1%
        AttackType.DNS_SPOOFING: 0.001,       # 0.1%
        AttackType.ZERO_DAY: 0.0001,          # 0.01% (rare)
    }
    
    # Attack characteristics
    ATTACK_CHARACTERISTICS = {
        AttackType.PORT_SCAN: {
            "description": "Scanning network ports to discover services",
            "packet_rate_range": (10.0, 100.0),  # packets/sec
            "packet_size_range": (40, 100),      # bytes
            "duration_range": (10, 60),          # seconds
            "target_ports": "all",
            "protocols": [Protocol.TCP, Protocol.UDP],
            "stealth_level": 0.7,                # 0-1, higher = stealthier
            "threat_score_range": (0.4, 0.7),
            "detection_difficulty": 0.3,         # 0-1, higher = harder to detect
        },
        AttackType.DDOS: {
            "description": "Distributed Denial of Service flood",
            "packet_rate_range": (500.0, 5000.0),
            "packet_size_range": (500, 1500),
            "duration_range": (30, 300),
            "target_ports": [80, 443, 53, 123],  # HTTP, HTTPS, DNS, NTP
            "protocols": [Protocol.UDP, Protocol.TCP, Protocol.ICMP],
            "amplification_possible": True,
            "threat_score_range": (0.8, 1.0),
            "detection_difficulty": 0.1,         # Easy to detect (high volume)
            "resource_consumption": 0.9,         # High resource impact
        },
        AttackType.MALWARE_SPREAD: {
            "description": "Malware propagation through network",
            "packet_rate_range": (1.0, 20.0),
            "packet_size_range": (1000, 10000),
            "duration_range": (60, 3600),
            "target_ports": [445, 139, 3389, 5900, 22],  # SMB, RDP, VNC, SSH
            "protocols": [Protocol.TCP],
            "encryption_probability": 0.6,
            "spread_rate": 0.3,                  # Chance to infect neighbor
            "threat_score_range": (0.7, 0.9),
            "detection_difficulty": 0.6,
        },
        AttackType.BRUTE_FORCE: {
            "description": "Password guessing attacks",
            "packet_rate_range": (5.0, 50.0),
            "packet_size_range": (100, 500),
            "duration_range": (30, 600),
            "target_ports": [22, 23, 3389, 5900, 21],  # SSH, Telnet, RDP, VNC, FTP
            "protocols": [Protocol.TCP],
            "credentials_per_second": 10,
            "success_rate": 0.001,               # Very low per attempt
            "threat_score_range": (0.5, 0.8),
            "detection_difficulty": 0.4,
        },
        AttackType.SQL_INJECTION: {
            "description": "SQL injection attacks on web applications",
            "packet_rate_range": (0.5, 5.0),
            "packet_size_range": (200, 2000),
            "duration_range": (10, 120),
            "target_ports": [80, 443, 8080],     # Web servers
            "protocols": [Protocol.HTTP, Protocol.HTTPS],
            "sql_patterns": [
                "' OR '1'='1",
                "'; DROP TABLE users; --",
                "UNION SELECT NULL, password FROM users",
                "1' AND '1'='1",
                "<script>alert('xss')</script>",
            ],
            "threat_score_range": (0.6, 0.9),
            "detection_difficulty": 0.5,
        },
        AttackType.SYN_FLOOD: {
            "description": "SYN flood attack (half-open connections)",
            "packet_rate_range": (100.0, 1000.0),
            "packet_size_range": (40, 60),       # SYN packets are small
            "duration_range": (60, 300),
            "target_ports": "any",
            "protocols": [Protocol.TCP],
            "spoof_source_ip": True,
            "threat_score_range": (0.7, 0.9),
            "detection_difficulty": 0.2,
            "resource_consumption": 0.8,
        },
    }
    
    # Attack patterns (how attacks evolve over time)
    ATTACK_PATTERNS = {
        "stealthy_recon": {
            "stages": [
                {"type": AttackType.PORT_SCAN, "duration": 30, "intensity": 0.3},
                {"type": AttackType.OS_FINGERPRINTING, "duration": 10, "intensity": 0.4},
                {"type": AttackType.VULNERABILITY_SCAN, "duration": 60, "intensity": 0.5},
            ],
            "description": "Stealthy reconnaissance before main attack"
        },
        "ddos_campaign": {
            "stages": [
                {"type": AttackType.PORT_SCAN, "duration": 10, "intensity": 0.2},
                {"type": AttackType.DDOS, "duration": 180, "intensity": 0.9},
                {"type": AttackType.BRUTE_FORCE, "duration": 60, "intensity": 0.6},
            ],
            "description": "DDoS followed by intrusion attempts"
        },
        "malware_outbreak": {
            "stages": [
                {"type": AttackType.MALWARE_SPREAD, "duration": 300, "intensity": 0.7},
                {"type": AttackType.DATA_EXFILTRATION, "duration": 120, "intensity": 0.8},
                {"type": AttackType.LATERAL_MOVEMENT, "duration": 180, "intensity": 0.6},
            ],
            "description": "Malware spread with data exfiltration"
        },
    }
    
    # Defense effectiveness against different attacks (0-1)
    DEFENSE_EFFECTIVENESS = {
        AttackType.PORT_SCAN: {
            "firewall": 0.8,
            "ids": 0.7,
            "ips": 0.9,
            "rate_limiting": 0.6,
        },
        AttackType.DDOS: {
            "firewall": 0.3,
            "ids": 0.4,
            "ips": 0.5,
            "rate_limiting": 0.9,
            "scrubbing_center": 0.95,
        },
        AttackType.MALWARE_SPREAD: {
            "firewall": 0.6,
            "ids": 0.8,
            "ips": 0.85,
            "antivirus": 0.9,
            "application_whitelisting": 0.95,
        },
        AttackType.BRUTE_FORCE: {
            "firewall": 0.4,
            "ids": 0.6,
            "ips": 0.7,
            "rate_limiting": 0.9,
            "multifactor_auth": 0.99,
        },
        AttackType.SQL_INJECTION: {
            "firewall": 0.5,
            "ids": 0.8,
            "ips": 0.85,
            "waf": 0.95,  # Web Application Firewall
        },
    }
    
    @classmethod
    def get_attack_config(cls, attack_type: AttackType) -> Dict[str, Any]:
        """Get configuration for a specific attack type"""
        return cls.ATTACK_CHARACTERISTICS.get(attack_type, {})
    
    @classmethod
    def get_attack_severity(cls, attack_type: AttackType) -> AttackSeverity:
        """Get severity level for attack type"""
        return cls.ATTACK_SEVERITY.get(attack_type, AttackSeverity.MEDIUM)
    
    @classmethod
    def get_attack_probability(cls, attack_type: AttackType) -> float:
        """Get probability for attack type"""
        return cls.ATTACK_PROBABILITIES.get(attack_type, 0.001)
    
    @classmethod
    def get_random_attack_type(cls) -> AttackType:
        """Get random attack type based on probabilities"""
        attack_types = list(cls.ATTACK_PROBABILITIES.keys())
        probabilities = list(cls.ATTACK_PROBABILITIES.values())
        return random.choices(attack_types, weights=probabilities, k=1)[0]
    
    @classmethod
    def get_attack_pattern(cls, pattern_name: str) -> Dict:
        """Get a predefined attack pattern"""
        return cls.ATTACK_PATTERNS.get(pattern_name)
    
    @classmethod
    def get_defense_effectiveness(cls, attack_type: AttackType, 
                                 defense_type: str) -> float:
        """Get effectiveness of a defense against attack type"""
        return cls.DEFENSE_EFFECTIVENESS.get(attack_type, {}).get(defense_type, 0.0)
    
    @classmethod
    def generate_attack_intensity(cls, attack_type: AttackType) -> float:
        """Generate intensity level for an attack (0.0-1.0)"""
        severity = cls.get_attack_severity(attack_type)
        
        # Higher severity attacks tend to have higher intensity
        if severity == AttackSeverity.CRITICAL:
            return random.uniform(0.8, 1.0)
        elif severity == AttackSeverity.HIGH:
            return random.uniform(0.6, 0.9)
        elif severity == AttackSeverity.MEDIUM:
            return random.uniform(0.4, 0.7)
        else:  # LOW
            return random.uniform(0.2, 0.5)
    
    @classmethod
    def get_recommended_defenses(cls, attack_type: AttackType) -> List[str]:
        """Get recommended defenses for an attack type"""
        defenses = cls.DEFENSE_EFFECTIVENESS.get(attack_type, {})
        # Return defenses with effectiveness > 0.7
        return [defense for defense, effectiveness in defenses.items() 
                if effectiveness > 0.7]