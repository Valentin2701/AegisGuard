from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import uuid
from datetime import datetime
import math
import random
from .config.enums import Protocol, PacketType, PacketStatus, Direction, QoSClass

@dataclass
class TCPFlags:
    """TCP control flags"""
    syn: bool = False
    ack: bool = False
    fin: bool = False
    rst: bool = False
    psh: bool = False
    urg: bool = False
    
    def to_dict(self) -> Dict[str, bool]:
        return {
            "syn": self.syn,
            "ack": self.ack,
            "fin": self.fin,
            "rst": self.rst,
            "psh": self.psh,
            "urg": self.urg
        }
    
    def to_int(self) -> int:
        """Convert flags to TCP flag integer representation"""
        flags = 0
        if self.fin: flags |= 0x01
        if self.syn: flags |= 0x02
        if self.rst: flags |= 0x04
        if self.psh: flags |= 0x08
        if self.ack: flags |= 0x10
        if self.urg: flags |= 0x20
        return flags
    
    @classmethod
    def from_int(cls, flag_int: int) -> 'TCPFlags':
        """Create from TCP flag integer"""
        return cls(
            fin=bool(flag_int & 0x01),
            syn=bool(flag_int & 0x02),
            rst=bool(flag_int & 0x04),
            psh=bool(flag_int & 0x08),
            ack=bool(flag_int & 0x10),
            urg=bool(flag_int & 0x20)
        )
    
    @classmethod
    def syn_ack(cls) -> 'TCPFlags':
        """SYN-ACK flags for TCP handshake"""
        return cls(syn=True, ack=True)
    
    @classmethod
    def syn(cls) -> 'TCPFlags':
        """SYN flag for connection initiation"""
        return cls(syn=True)
    
    @classmethod
    def ack(cls) -> 'TCPFlags':
        """ACK flag for data acknowledgment"""
        return cls(ack=True)
    
    @classmethod
    def fin_ack(cls) -> 'TCPFlags':
        """FIN-ACK for connection termination"""
        return cls(fin=True, ack=True)

@dataclass
class Packet:
    """
    Represents a network packet with real-world attributes
    """
    # Core identification
    packet_id: str
    flow_id: Optional[str] = None  # For tracking flows/sessions
    source_id: str = ""
    destination_id: str = ""
    
    # Network layer
    source_ip: str = ""
    destination_ip: str = ""
    source_port: Optional[int] = None
    destination_port: Optional[int] = None
    protocol: Protocol = Protocol.TCP
    packet_type: PacketType = PacketType.DATA
    
    # Transport layer
    tcp_flags: TCPFlags = field(default_factory=TCPFlags)
    sequence_number: int = 0
    acknowledgment_number: int = 0
    window_size: int = 65535
    checksum: int = 0
    
    # Content
    payload: str = ""
    payload_size: int = 0  # bytes
    payload_entropy: float = 0.0  # 0-1, randomness of payload
    
    # QoS and routing
    direction: Direction = Direction.OUTBOUND
    qos_class: QoSClass = QoSClass.BEST_EFFORT
    dscp: int = 0  # Differentiated Services Code Point (0-63)
    ecn_marked: bool = False  # Explicit Congestion Notification
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    ttl: int = 64  # Time To Live
    requires_ack: bool = True
    
    # Transmission info
    status: PacketStatus = PacketStatus.CREATED
    current_node: Optional[str] = None
    path_taken: List[str] = field(default_factory=list)
    latency_accumulated: float = 0.0  # ms
    jitter: float = 0.0  # Variation in latency
    
    # Security
    is_encrypted: bool = False
    encryption_strength: int = 0  # 0-100
    is_malicious: bool = False
    threat_score: float = 0.0  # 0-1
    vlan_id: Optional[int] = None  # VLAN tagging
    
    def __post_init__(self):
        """Initialize derived fields"""
        if not self.flow_id:
            # Generate flow ID from 5-tuple
            self.flow_id = self._generate_flow_id()
        
        if self.payload and not self.payload_size:
            self.payload_size = len(self.payload.encode('utf-8'))
        
        if self.payload and self.payload_entropy == 0.0:
            self.payload_entropy = self._calculate_entropy(self.payload)
        
        if not self.source_ip and self.source_id:
            # Try to get IP from node if available
            pass  # We'll handle this in traffic generator
        
        if not self.destination_ip and self.destination_id:
            pass  # We'll handle this in traffic generator
    
    def _generate_flow_id(self) -> str:
        """Generate flow ID from 5-tuple"""
        src_port = self.source_port or 0
        dst_port = self.destination_port or 0
        return f"{self.source_ip}:{src_port}-{self.destination_ip}:{dst_port}-{self.protocol.value}"
    
    @staticmethod
    def _calculate_entropy(data: str) -> float:
        """Calculate Shannon entropy of payload (0-1 scale)"""
        if not data:
            return 0.0
        
        # Count frequency of each byte
        freq = {}
        for byte in data.encode('utf-8'):
            freq[byte] = freq.get(byte, 0) + 1
        
        # Calculate entropy
        entropy = 0.0
        total_len = len(data)
        for count in freq.values():
            probability = count / total_len
            entropy -= probability * math.log2(probability)
        
        # Normalize to 0-1 (max entropy for bytes is 8 bits)
        return entropy / 8.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert packet to dictionary with all real-world attributes"""
        return {
            # Core
            "id": self.packet_id,
            "flow_id": self.flow_id,
            
            # Network layer
            "source": self.source_id,
            "destination": self.destination_id,
            "source_ip": self.source_ip,
            "destination_ip": self.destination_ip,
            "source_port": self.source_port,
            "destination_port": self.destination_port,
            "protocol": self.protocol.value,
            "type": self.packet_type.value,
            
            # Transport layer
            "tcp_flags": self.tcp_flags.to_dict(),
            "tcp_flags_int": self.tcp_flags.to_int(),
            "seq_num": self.sequence_number,
            "ack_num": self.acknowledgment_number,
            "window": self.window_size,
            "checksum": self.checksum,
            
            # Content
            "payload_size": self.payload_size,
            "payload_entropy": self.payload_entropy,
            
            # QoS
            "direction": self.direction.value,
            "qos_class": self.qos_class.value,
            "dscp": self.dscp,
            "ecn_marked": self.ecn_marked,
            
            # Metadata
            "timestamp": self.timestamp.isoformat(),
            "ttl": self.ttl,
            "status": self.status.value,
            "current_node": self.current_node,
            "path_taken": self.path_taken.copy(),
            "latency_ms": self.latency_accumulated,
            "jitter_ms": self.jitter,
            
            # Security
            "is_encrypted": self.is_encrypted,
            "encryption_strength": self.encryption_strength,
            "is_malicious": self.is_malicious,
            "threat_score": self.threat_score,
            "vlan_id": self.vlan_id,
            "requires_ack": self.requires_ack
        }
    
    @classmethod
    def create_tcp_connection_syn(cls, source: str, destination: str, 
                                 source_port: int, dest_port: int) -> 'Packet':
        """Create TCP SYN packet for connection initiation"""
        return cls(
            packet_id=f"tcp_syn_{uuid.uuid4().hex[:8]}",
            source_id=source,
            destination_id=destination,
            source_port=source_port,
            destination_port=dest_port,
            protocol=Protocol.TCP,
            tcp_flags=TCPFlags.syn(),
            sequence_number=random.randint(1000, 9999),
            payload_size=0,
            direction=Direction.OUTBOUND
        )
    
    @classmethod
    def create_tcp_data_packet(cls, flow_id: str, seq_num: int, ack_num: int,
                              payload: str = "", psh: bool = True) -> 'Packet':
        """Create TCP data packet with proper sequencing"""
        # Parse flow ID to get connection details
        parts = flow_id.split('-')
        if len(parts) >= 3:
            src_part, dst_part, proto = parts
            src_ip_port = src_part.split(':')
            dst_ip_port = dst_part.split(':')
            
            return cls(
                packet_id=f"tcp_data_{uuid.uuid4().hex[:8]}",
                flow_id=flow_id,
                source_ip=src_ip_port[0],
                source_port=int(src_ip_port[1]) if len(src_ip_port) > 1 else None,
                destination_ip=dst_ip_port[0],
                destination_port=int(dst_ip_port[1]) if len(dst_ip_port) > 1 else None,
                protocol=Protocol(proto.lower()),
                tcp_flags=TCPFlags(ack=True, psh=psh),
                sequence_number=seq_num,
                acknowledgment_number=ack_num,
                payload=payload,
                payload_size=len(payload.encode('utf-8')),
                direction=Direction.OUTBOUND
            )
        return None
    
    @classmethod
    def create_udp_packet(cls, source: str, destination: str,
                         source_port: int, dest_port: int,
                         payload: str = "") -> 'Packet':
        """Create UDP packet"""
        return cls(
            packet_id=f"udp_{uuid.uuid4().hex[:8]}",
            source_id=source,
            destination_id=destination,
            source_port=source_port,
            destination_port=dest_port,
            protocol=Protocol.UDP,
            payload=payload,
            payload_size=len(payload.encode('utf-8')),
            direction=Direction.OUTBOUND
        )
    
    @classmethod
    def create_icmp_packet(cls, source: str, destination: str,
                          icmp_type: int = 8,  # 8 = echo request
                          code: int = 0) -> 'Packet':
        """Create ICMP packet (ping)"""
        return cls(
            packet_id=f"icmp_{uuid.uuid4().hex[:8]}",
            source_id=source,
            destination_id=destination,
            protocol=Protocol.ICMP,
            payload=f"ICMP type={icmp_type} code={code}",
            payload_size=56,  # Standard ping size
            direction=Direction.OUTBOUND
        )
    
    @classmethod
    def create_dns_query(cls, source: str, destination: str,
                        query: str = "example.com") -> 'Packet':
        """Create DNS query packet"""
        return cls(
            packet_id=f"dns_{uuid.uuid4().hex[:8]}",
            source_id=source,
            destination_id=destination,
            source_port=random.randint(49152, 65535),  # Ephemeral port
            destination_port=53,  # DNS port
            protocol=Protocol.DNS,
            payload=f"DNS query: {query}",
            payload_size=len(query) + 12,  # DNS header overhead
            direction=Direction.OUTBOUND,
            qos_class=QoSClass.STANDARD
        )
    
    @classmethod
    def create_attack_packet(cls, source: str, destination: str,
                            attack_type: str, threat_score: float = 0.8) -> 'Packet':
        """Create attack packet with realistic attributes"""
        # Different attack types have different characteristics
        if attack_type == "port_scan":
            return cls(
                packet_id=f"atk_{uuid.uuid4().hex[:8]}",
                source_id=source,
                destination_id=destination,
                source_port=random.randint(1024, 65535),
                destination_port=random.randint(1, 1024),  # Scan well-known ports
                protocol=random.choice([Protocol.TCP, Protocol.UDP]),
                tcp_flags=TCPFlags(syn=True) if random.random() > 0.5 else TCPFlags(),
                payload="PORT_SCAN",
                payload_size=random.randint(40, 100),
                payload_entropy=random.uniform(0.3, 0.6),
                is_malicious=True,
                threat_score=threat_score,
                requires_ack=False,
                direction=Direction.OUTBOUND
            )
        
        elif attack_type == "ddos":
            return cls(
                packet_id=f"ddos_{uuid.uuid4().hex[:8]}",
                source_id=source,
                destination_id=destination,
                source_port=random.randint(1024, 65535),
                destination_port=random.choice([80, 443, 53]),  # Common DDoS targets
                protocol=Protocol.UDP,  # Common for amplification attacks
                payload="DDoS" * random.randint(10, 100),
                payload_size=random.randint(500, 1500),
                payload_entropy=random.uniform(0.7, 0.9),  # High entropy for DDoS
                is_malicious=True,
                threat_score=threat_score,
                requires_ack=False,
                direction=Direction.OUTBOUND,
                dscp=0  # Best effort (flood)
            )
        
        elif attack_type == "brute_force":
            return cls(
                packet_id=f"brute_{uuid.uuid4().hex[:8]}",
                source_id=source,
                destination_id=destination,
                source_port=random.randint(1024, 65535),
                destination_port=random.choice([22, 23, 3389]),  # SSH, Telnet, RDP
                protocol=Protocol.TCP,
                tcp_flags=TCPFlags(ack=True, psh=True),
                payload="LOGIN_ATTEMPT",
                payload_size=random.randint(50, 200),
                payload_entropy=random.uniform(0.4, 0.7),
                is_malicious=True,
                threat_score=threat_score,
                direction=Direction.OUTBOUND
            )
        
        # Generic attack packet
        return cls(
            packet_id=f"atk_{uuid.uuid4().hex[:8]}",
            source_id=source,
            destination_id=destination,
            packet_type=PacketType.ATTACK,
            payload=f"Attack: {attack_type}",
            protocol=Protocol.TCP,
            is_malicious=True,
            threat_score=threat_score,
            requires_ack=False,
            direction=Direction.OUTBOUND
        )
    
    def update_status(self, new_status: PacketStatus, node_id: Optional[str] = None):
        """Update packet status and track path"""
        self.status = new_status
        if node_id and node_id not in self.path_taken:
            self.path_taken.append(node_id)
        if node_id:
            self.current_node = node_id
    
    def decrement_ttl(self) -> bool:
        """Decrement TTL, return True if packet should be dropped"""
        self.ttl -= 1
        if self.ttl <= 0:
            self.status = PacketStatus.DROPPED
            return True
        return False
    
    def get_transit_time(self, edge_latency: float) -> float:
        """Calculate transit time over an edge with jitter"""
        # Add realistic jitter (10% of latency)
        self.jitter = random.uniform(-0.1, 0.1) * edge_latency
        return edge_latency + self.jitter
    
    def is_tcp_handshake(self) -> bool:
        """Check if this is a TCP handshake packet"""
        return self.tcp_flags.syn
    
    def is_tcp_fin(self) -> bool:
        """Check if this is a TCP FIN packet"""
        return self.tcp_flags.fin
    
    def is_tcp_rst(self) -> bool:
        """Check if this is a TCP RST packet"""
        return self.tcp_flags.rst
    
    def __str__(self) -> str:
        ports = f":{self.source_port}→{self.destination_port}" if self.source_port else ""
        flags = ""
        if self.protocol == Protocol.TCP:
            flags = " [" + "".join([f.upper() for f in ['S','A','F','R','P','U'] 
                                   if getattr(self.tcp_flags, f.lower())]) + "]"
        
        return (f"Packet[{self.packet_id[:8]}] "
                f"{self.source_id}{ports}→{self.destination_id} "
                f"({self.protocol.value}{flags})")