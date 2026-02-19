import random
import time
from typing import List, Dict, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict

from .packet import Packet, TCPFlags
from .config.enums import Protocol, Direction, QoSClass, TrafficPattern
from .network_graph import NetworkGraph

class Connection:
    """Represents a network connection/flow"""
    
    def __init__(self, conn_id: str, source_id: str, destination_id: str,
                 source_ip: str, dest_ip: str, protocol: Protocol,
                 source_port: int, dest_port: int, pattern: TrafficPattern):
        self.conn_id = conn_id
        self.source_id = source_id
        self.destination_id = destination_id
        self.source_ip = source_ip
        self.dest_ip = dest_ip
        self.protocol = protocol
        self.source_port = source_port
        self.dest_port = dest_port
        self.pattern = pattern
        
        # TCP state
        self.tcp_state = "CLOSED"  # CLOSED, SYN_SENT, ESTABLISHED, FIN_WAIT, etc.
        self.next_seq = random.randint(1000, 9999)
        self.next_ack = 0
        self.flow_id = f"{source_ip}:{source_port}-{dest_ip}:{dest_port}-{protocol.value}"
        
        # Statistics
        self.packets_sent = 0
        self.bytes_sent = 0
        self.start_time = datetime.now()
        self.last_activity = datetime.now()
        
        # QoS
        self.qos_class = self._determine_qos_class(pattern)
        self.dscp = self._determine_dscp()
    
    def _determine_qos_class(self, pattern: TrafficPattern) -> QoSClass:
        """Determine QoS class based on traffic pattern"""
        if "video" in pattern.name:
            return QoSClass.VIDEO
        elif "voice" in pattern.name or pattern.name == "voip":
            return QoSClass.VOICE
        elif "database" in pattern.name or "query" in pattern.name:
            return QoSClass.CRITICAL
        elif "web" in pattern.name:
            return QoSClass.STANDARD
        elif "email" in pattern.name or "file" in pattern.name:
            return QoSClass.BACKGROUND
        else:
            return QoSClass.BEST_EFFORT
    
    def _determine_dscp(self) -> int:
        """Determine DSCP value based on QoS class"""
        dscp_map = {
            QoSClass.NETWORK_CONTROL: 48,   # CS6
            QoSClass.CRITICAL: 46,          # EF
            QoSClass.VOICE: 46,             # EF
            QoSClass.VIDEO: 34,             # AF41
            QoSClass.STANDARD: 0,           # BE
            QoSClass.BACKGROUND: 8,         # CS1
            QoSClass.BEST_EFFORT: 0,        # BE
        }
        return dscp_map.get(self.qos_class, 0)
    
    def get_flow_id(self) -> str:
        """Get 5-tuple flow identifier"""
        return self.flow_id

class TrafficGenerator:
    """Generates realistic network traffic with flow tracking"""
    
    def __init__(self, network: NetworkGraph):
        self.network = network
        self.packets: List[Packet] = []
        self.connections: Dict[str, Connection] = {}
        self.active_flows: Set[str] = set()
        self.flow_counter = 0
        
        # Port allocation tracking
        self.used_ports: Dict[str, Set[int]] = defaultdict(set)
        
        # Statistics
        self.traffic_stats = {
            "total_packets": 0,
            "total_bytes": 0,
            "packets_delivered": 0,
            "packets_dropped": 0,
            "tcp_connections": 0,
            "udp_flows": 0,
            "avg_latency": 0.0,
            "peak_bandwidth": 0.0
        }
        
        # Protocol distributions (realistic internet mix)
        self.protocol_distribution = {
            Protocol.TCP: 0.85,    # Most traffic is TCP
            Protocol.UDP: 0.12,    # DNS, VoIP, streaming
            Protocol.ICMP: 0.01,   # Ping, traceroute
            Protocol.DNS: 0.02,    # DNS queries
        }
        
        # Common port ranges for services
        self.service_ports = {
            "http": 80,
            "https": 443,
            "ssh": 22,
            "ftp": 21,
            "smtp": 25,
            "dns": 53,
            "dhcp": 67,
            "pop3": 110,
            "imap": 143,
            "mysql": 3306,
            "postgresql": 5432,
            "rdp": 3389,
        }
    
    def _allocate_port(self, node_id: str) -> int:
        """Allocate an ephemeral port for a node"""
        # Ephemeral ports (IANA range)
        port_range = (49152, 65535)
        
        if node_id not in self.used_ports:
            self.used_ports[node_id] = set()
        
        used = self.used_ports[node_id]
        
        # Try to find an unused port
        for _ in range(100):
            port = random.randint(*port_range)
            if port not in used:
                used.add(port)
                return port
        
        # Fallback: reuse a port (happens in real networks)
        return random.randint(*port_range)
    
    def create_connection(self, source_id: str, destination_id: str,
                         pattern: TrafficPattern) -> Optional[Connection]:
        """Create a realistic network connection"""
        source_node = self.network.get_node(source_id)
        dest_node = self.network.get_node(destination_id)
        
        if not source_node or not dest_node:
            return None
        
        if source_id == destination_id:
            return None  # No self-connections
        
        if not pattern:
            pattern = random.choice(list(TrafficPattern))
        
        # Determine protocol based on pattern
        if pattern.protocol == "TCP":
            protocol = Protocol.TCP
        elif pattern.protocol == "UDP":
            protocol = Protocol.UDP
        elif pattern.protocol == "DNS":
            protocol = Protocol.DNS
        else:
            protocol = random.choices(
                list(self.protocol_distribution.keys()),
                weights=list(self.protocol_distribution.values())
            )[0]
        
        # Allocate ports
        source_port = self._allocate_port(source_id)
        
        # Determine destination port based on services
        dest_port = None
        if dest_node.services:
            # Try to match a service
            for service in dest_node.services:
                if service in self.service_ports:
                    dest_port = self.service_ports[service]
                    break
        
        # Fallback to random well-known port
        if dest_port is None:
            dest_port = random.choice(list(self.service_ports.values()))
        
        # Create connection ID
        conn_id = f"conn_{source_id}_{destination_id}_{protocol.value}_{int(time.time())}"
        
        # Create connection object
        connection = Connection(
            conn_id=conn_id,
            source_id=source_id,
            destination_id=destination_id,
            source_ip=source_node.ip_address,
            dest_ip=dest_node.ip_address,
            protocol=protocol,
            source_port=source_port,
            dest_port=dest_port,
            pattern=pattern
        )
        
        self.connections[conn_id] = connection
        self.active_flows.add(connection.get_flow_id())
        
        # Update statistics
        if protocol == Protocol.TCP:
            self.traffic_stats["tcp_connections"] += 1
        elif protocol == Protocol.UDP:
            self.traffic_stats["udp_flows"] += 1
        
        # Update edge traffic
        edge = self.network.get_edge(source_id, destination_id)
        if edge:
            edge.traffic_volume += pattern.packet_rate * pattern.avg_packet_size / 8
        
        return connection
    
    def _generate_tcp_packets(self, connection: Connection, 
                             time_delta: float) -> List[Packet]:
        """Generate TCP packets for a connection"""
        packets = []
        
        # Calculate expected packets
        expected_packets = connection.pattern.packet_rate * time_delta
        packets_to_generate = int(expected_packets)
        
        if random.random() < (expected_packets - packets_to_generate):
            packets_to_generate += 1
        
        # TCP State Machine
        if connection.tcp_state == "CLOSED":
            # Send SYN
            syn_packet = Packet.create_tcp_connection_syn(
                source=connection.source_id,
                destination=connection.destination_id,
                source_port=connection.source_port,
                dest_port=connection.dest_port
            )
            syn_packet.source_ip = connection.source_ip
            syn_packet.destination_ip = connection.dest_ip
            syn_packet.qos_class = connection.qos_class
            syn_packet.dscp = connection.dscp
            syn_packet.flow_id = connection.get_flow_id()
            
            packets.append(syn_packet)
            connection.tcp_state = "SYN_SENT"
            connection.next_seq += 1
            
        elif connection.tcp_state == "SYN_SENT":
            # Send SYN-ACK (simulating response from server)
            syn_ack = Packet(
                packet_id=f"tcp_sa_{connection.conn_id[:8]}",
                flow_id=connection.get_flow_id(),
                source_id=connection.destination_id,  # Server responds
                destination_id=connection.source_id,
                source_ip=connection.dest_ip,
                destination_ip=connection.source_ip,
                source_port=connection.dest_port,
                destination_port=connection.source_port,
                protocol=Protocol.TCP,
                tcp_flags=TCPFlags.syn_ack(),
                sequence_number=random.randint(1000, 9999),
                acknowledgment_number=connection.next_seq,
                qos_class=connection.qos_class,
                dscp=connection.dscp,
                direction=Direction.INBOUND
            )
            packets.append(syn_ack)
            connection.tcp_state = "ESTABLISHED"
            connection.next_ack = syn_ack.sequence_number + 1
            
        elif connection.tcp_state == "ESTABLISHED":
            # Generate data packets
            for _ in range(packets_to_generate):
                # Create payload
                payload_size = max(64, int(random.gauss(
                    connection.pattern.avg_packet_size,
                    connection.pattern.avg_packet_size * 0.1
                )))
                
                # Simulate different types of data
                if connection.pattern.name == "web_browsing":
                    payload = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<html>"
                    entropy = random.uniform(0.4, 0.7)
                elif connection.pattern.name == "database":
                    payload = '{"query":"SELECT * FROM users", "result":[...]}'
                    entropy = random.uniform(0.5, 0.8)
                elif connection.pattern.name == "video_streaming":
                    payload = "RTP/AVP video data"
                    entropy = random.uniform(0.7, 0.9)  # Encrypted/compressed
                else:
                    payload = f"{connection.pattern.name} data {random.randint(1, 1000)}"
                    entropy = random.uniform(0.3, 0.6)
                
                # Create data packet
                data_packet = Packet.create_tcp_data_packet(
                    flow_id=connection.get_flow_id(),
                    seq_num=connection.next_seq,
                    ack_num=connection.next_ack,
                    payload=payload[:payload_size],
                    psh=(random.random() > 0.7)  # 30% chance of PSH flag
                )
                
                if data_packet:
                    data_packet.source_id = connection.source_id
                    data_packet.destination_id = connection.destination_id
                    data_packet.qos_class = connection.qos_class
                    data_packet.dscp = connection.dscp
                    data_packet.payload_entropy = entropy
                    
                    # Encryption for certain protocols
                    if connection.pattern.protocol in ["HTTPS", "TLS"]:
                        data_packet.is_encrypted = True
                        data_packet.encryption_strength = random.randint(80, 100)
                    
                    packets.append(data_packet)
                    
                    # Update sequence numbers
                    connection.next_seq += len(payload.encode('utf-8'))
                    connection.packets_sent += 1
                    connection.bytes_sent += payload_size
        
        # Randomly close connections (simulating end of session)
        if connection.tcp_state == "ESTABLISHED" and random.random() < 0.01 * time_delta:
            fin_packet = Packet(
                packet_id=f"tcp_fin_{connection.conn_id[:8]}",
                flow_id=connection.get_flow_id(),
                source_id=connection.source_id,
                destination_id=connection.destination_id,
                source_ip=connection.source_ip,
                destination_ip=connection.dest_ip,
                source_port=connection.source_port,
                destination_port=connection.dest_port,
                protocol=Protocol.TCP,
                tcp_flags=TCPFlags.fin_ack(),
                sequence_number=connection.next_seq,
                acknowledgment_number=connection.next_ack,
                qos_class=connection.qos_class,
                dscp=connection.dscp,
                direction=Direction.OUTBOUND
            )
            packets.append(fin_packet)
            connection.tcp_state = "FIN_WAIT"
            connection.next_seq += 1
        
        return packets
    
    def _generate_udp_packets(self, connection: Connection,
                             time_delta: float) -> List[Packet]:
        """Generate UDP packets for a connection"""
        packets = []
        
        expected_packets = connection.pattern.packet_rate * time_delta
        packets_to_generate = int(expected_packets)
        
        if random.random() < (expected_packets - packets_to_generate):
            packets_to_generate += 1
        
        for _ in range(packets_to_generate):
            payload_size = max(64, int(random.gauss(
                connection.pattern.avg_packet_size,
                connection.pattern.avg_packet_size * 0.15  # More variation for UDP
            )))
            
            # Create UDP packet
            udp_packet = Packet.create_udp_packet(
                source=connection.source_id,
                destination=connection.destination_id,
                source_port=connection.source_port,
                dest_port=connection.dest_port,
                payload=f"UDP {connection.pattern.name} {random.randint(1, 1000)}"
            )
            
            udp_packet.source_ip = connection.source_ip
            udp_packet.destination_ip = connection.dest_ip
            udp_packet.qos_class = connection.qos_class
            udp_packet.dscp = connection.dscp
            udp_packet.payload_entropy = random.uniform(0.5, 0.8)
            udp_packet.payload_size = payload_size
            
            packets.append(udp_packet)
            connection.packets_sent += 1
            connection.bytes_sent += payload_size
        
        return packets
    
    def generate_packets(self, time_delta: float = 1.0) -> List[Packet]:
        """Generate packets for all active connections"""
        new_packets = []
        
        for connection in list(self.connections.values()):
            if connection.protocol == Protocol.TCP:
                packets = self._generate_tcp_packets(connection, time_delta)
            elif connection.protocol == Protocol.UDP:
                packets = self._generate_udp_packets(connection, time_delta)
            elif connection.protocol == Protocol.DNS:
                # Special handling for DNS
                if random.random() < 0.1 * time_delta:  # DNS queries are less frequent
                    dns_packet = Packet.create_dns_query(
                        source=connection.source_id,
                        destination=connection.destination_id,
                        query=f"server{random.randint(1, 10)}.example.com"
                    )
                    dns_packet.source_ip = connection.source_ip
                    dns_packet.destination_ip = connection.dest_ip
                    dns_packet.qos_class = connection.qos_class
                    packets = [dns_packet]
                else:
                    packets = []
            else:
                # Generic packet generation
                packets = []
            
            new_packets.extend(packets)
            connection.last_activity = datetime.now()
        
        # Update statistics
        self.packets.extend(new_packets)
        self.traffic_stats["total_packets"] += len(new_packets)
        self.traffic_stats["total_bytes"] += sum(
            p.payload_size for p in new_packets if hasattr(p, 'payload_size')
        )
        
        # Clean up old connections (simulate connection timeout)
        self._cleanup_old_connections(time_delta * 10)  # Scale timeout with time delta
        
        return new_packets
    
    def _cleanup_old_connections(self, max_idle_seconds: int = 300):
        """Remove connections that have been idle too long"""
        now = datetime.now()
        to_remove = []
        
        for conn_id, connection in self.connections.items():
            idle_time = (now - connection.last_activity).total_seconds()
            if idle_time > max_idle_seconds:
                to_remove.append(conn_id)
        
        for conn_id in to_remove:
            connection = self.connections[conn_id]
            self.active_flows.discard(connection.get_flow_id())
            del self.connections[conn_id]
    
    def get_traffic_stats(self) -> Dict:
        """Get current traffic statistics"""
        # Calculate additional stats
        delivered = [p for p in self.packets if p.status.name == "DELIVERED"]
        dropped = [p for p in self.packets if p.status.name == "DROPPED"]
        
        if delivered:
            avg_latency = sum(p.latency_accumulated for p in delivered) / len(delivered)
        else:
            avg_latency = 0.0
        
        # Calculate current bandwidth
        current_bytes = sum(p.payload_size for p in self.packets[-100:] if hasattr(p, 'payload_size'))
        current_bandwidth = (current_bytes * 8) / 1_000_000  # Mbps
        
        return {
            **self.traffic_stats,
            "packets_delivered": len(delivered),
            "packets_dropped": len(dropped),
            "avg_latency_ms": avg_latency,
            "current_bandwidth_mbps": current_bandwidth,
            "active_connections": len(self.connections),
            "unique_flows": len(self.active_flows)
        }
    
    def clear(self):
        """Clear all traffic data"""
        self.packets.clear()
        self.connections.clear()
        self.active_flows.clear()
        self.used_ports.clear()
        self.flow_counter = 0
        
        # Reset stats
        self.traffic_stats = {
            "total_packets": 0,
            "total_bytes": 0,
            "packets_delivered": 0,
            "packets_dropped": 0,
            "tcp_connections": 0,
            "udp_flows": 0,
            "avg_latency": 0.0,
            "peak_bandwidth": 0.0,
            "active_connections": 0
        }