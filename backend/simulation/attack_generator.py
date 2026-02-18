import random
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from .config.enums import AttackType, Protocol, PacketType, Direction
from .packet import Packet, TCPFlags
from .network_graph import NetworkGraph

class Attack:
    """Represents a cyber attack"""
    
    def __init__(self, attack_id: str, attack_type: AttackType, 
                 source_id: str, target_id: str, intensity: float = 0.7):
        self.attack_id = attack_id
        self.attack_type = attack_type
        self.source_id = source_id
        self.target_id = target_id
        self.intensity = intensity  # 0.0 to 1.0
        
        # Attack state
        self.start_time = datetime.now()
        self.is_active = True
        self.detected = False
        self.stopped = False
        
        # Statistics
        self.packets_sent = 0
        self.bytes_sent = 0
        self.damage_caused = 0.0  # 0-100 scale
        self.detection_time = None
        
        # Attack-specific parameters
        self._init_attack_parameters()
    
    def _init_attack_parameters(self):
        """Initialize attack-specific parameters"""
        self.parameters = {
            "packet_rate": 0.0,
            "packet_size": 0,
            "target_ports": [],
            "scan_range": (1, 1024),
            "flood_duration": 0,
        }
        
        if self.attack_type == AttackType.PORT_SCAN:
            self.parameters.update({
                "packet_rate": 50.0 * self.intensity,
                "packet_size": 100,
                "scan_range": (1, 1024 if self.intensity < 0.5 else 65535),
                "stealth_mode": random.random() > 0.3,  # 70% chance stealth
            })
        
        elif self.attack_type == AttackType.DDOS:
            self.parameters.update({
                "packet_rate": 1000.0 * self.intensity,
                "packet_size": random.randint(500, 1500),
                "flood_duration": random.randint(30, 300),  # 30s to 5min
                "amplification_factor": random.uniform(1.0, 50.0),
            })
        
        elif self.attack_type == AttackType.MALWARE_SPREAD:
            self.parameters.update({
                "packet_rate": 10.0 * self.intensity,
                "packet_size": random.randint(1000, 10000),
                "spread_rate": 0.3 * self.intensity,
                "encrypted_payload": random.random() > 0.5,
            })
        
        elif self.attack_type == AttackType.BRUTE_FORCE:
            self.parameters.update({
                "packet_rate": 20.0 * self.intensity,
                "packet_size": random.randint(100, 500),
                "target_ports": [22, 23, 3389, 5900],  # SSH, Telnet, RDP, VNC
                "credentials_tried": 0,
            })
        
        elif self.attack_type == AttackType.SQL_INJECTION:
            self.parameters.update({
                "packet_rate": 5.0 * self.intensity,
                "payload_size": random.randint(200, 2000),
                "sql_patterns": [
                    "' OR '1'='1",
                    "'; DROP TABLE users; --",
                    "UNION SELECT NULL, password FROM users",
                    "<script>alert('xss')</script>",
                ]
            })
    
    def generate_packets(self, time_delta: float) -> List[Packet]:
        """Generate attack packets for this time period"""
        if not self.is_active or self.stopped:
            return []
        
        packets = []
        expected_packets = self.parameters["packet_rate"] * time_delta
        packets_to_generate = int(expected_packets)
        
        # Handle fractional packets
        if random.random() < (expected_packets - packets_to_generate):
            packets_to_generate += 1
        
        for _ in range(packets_to_generate):
            packet = self._create_attack_packet()
            if packet:
                packets.append(packet)
                self.packets_sent += 1
                self.bytes_sent += packet.payload_size
        
        # Update attack state
        self._update_attack_state(time_delta)
        
        return packets
    
    def _create_attack_packet(self) -> Optional[Packet]:
        """Create a single attack packet based on attack type"""
        try:
            if self.attack_type == AttackType.PORT_SCAN:
                return self._create_port_scan_packet()
            elif self.attack_type == AttackType.DDOS:
                return self._create_ddos_packet()
            elif self.attack_type == AttackType.MALWARE_SPREAD:
                return self._create_malware_packet()
            elif self.attack_type == AttackType.BRUTE_FORCE:
                return self._create_brute_force_packet()
            elif self.attack_type == AttackType.SQL_INJECTION:
                return self._create_sql_injection_packet()
            else:
                return self._create_generic_attack_packet()
        except Exception:
            return None
    
    def _create_port_scan_packet(self) -> Packet:
        """Create a port scanning packet"""
        stealth = self.parameters.get("stealth_mode", False)
        
        if stealth and random.random() > 0.7:
            # Stealth scan: TCP SYN
            flags = TCPFlags(syn=True)
            requires_ack = True
        else:
            # Regular scan: varies
            scan_types = [
                (TCPFlags(syn=True), True),      # SYN scan
                (TCPFlags(ack=True), False),     # ACK scan
                (TCPFlags(fin=True), False),     # FIN scan
                (TCPFlags(), False),             # NULL scan
            ]
            flags, requires_ack = random.choice(scan_types)
        
        # Random target port
        min_port, max_port = self.parameters["scan_range"]
        target_port = random.randint(min_port, max_port)
        
        return Packet(
            packet_id=f"scan_{self.attack_id}_{self.packets_sent:06d}",
            source_id=self.source_id,
            destination_id=self.target_id,
            source_port=random.randint(49152, 65535),
            destination_port=target_port,
            protocol=Protocol.TCP,
            packet_type=PacketType.ATTACK,
            tcp_flags=flags,
            payload=f"Port scan: {target_port}",
            payload_size=self.parameters["packet_size"],
            is_malicious=True,
            threat_score=0.6 + (0.4 * self.intensity),
            requires_ack=requires_ack,
            direction=Direction.OUTBOUND,
            payload_entropy=random.uniform(0.3, 0.6),
        )
    
    def _create_ddos_packet(self) -> Packet:
        """Create a DDoS attack packet"""
        # Common DDoS techniques
        ddos_types = [
            ("UDP flood", Protocol.UDP, 0, False),
            ("ICMP flood", Protocol.ICMP, 0, False),
            ("SYN flood", Protocol.TCP, TCPFlags(syn=True).to_int(), True),
            ("HTTP flood", Protocol.HTTP, 0, True),
        ]
        
        attack_name, protocol, tcp_flags_int, has_payload = random.choice(ddos_types)
        
        if has_payload:
            payload = f"DDoS: {attack_name} " + "X" * random.randint(100, 1000)
            payload_size = len(payload.encode('utf-8'))
        else:
            payload = ""
            payload_size = self.parameters["packet_size"]
        
        return Packet(
            packet_id=f"ddos_{self.attack_id}_{self.packets_sent:06d}",
            source_id=self.source_id,
            destination_id=self.target_id,
            source_port=random.randint(1024, 65535),
            destination_port=random.choice([80, 443, 53, 123]),  # Common targets
            protocol=protocol,
            packet_type=PacketType.ATTACK,
            payload=payload,
            payload_size=payload_size,
            is_malicious=True,
            threat_score=0.8 + (0.2 * self.intensity),
            requires_ack=False,
            direction=Direction.OUTBOUND,
            payload_entropy=random.uniform(0.7, 0.9),  # High entropy for floods
        )
    
    def _create_malware_packet(self) -> Packet:
        """Create a malware propagation packet"""
        encrypted = self.parameters.get("encrypted_payload", False)
        
        malware_types = [
            "Trojan-Dropper",
            "Ransomware-Encryptor",
            "Botnet-C2",
            "Keylogger-Exfil",
            "Worm-Propagate",
        ]
        
        malware_type = random.choice(malware_types)
        payload = f"MALWARE:{malware_type}:{random.getrandbits(128):032x}"
        
        return Packet(
            packet_id=f"mal_{self.attack_id}_{self.packets_sent:06d}",
            source_id=self.source_id,
            destination_id=self.target_id,
            source_port=random.randint(1024, 65535),
            destination_port=random.choice([445, 139, 3389, 5900]),  # Common malware ports
            protocol=Protocol.TCP,
            packet_type=PacketType.ATTACK,
            tcp_flags=TCPFlags(ack=True, psh=True),
            payload=payload,
            payload_size=self.parameters["packet_size"],
            is_malicious=True,
            threat_score=0.9,
            is_encrypted=encrypted,
            encryption_strength=random.randint(70, 95) if encrypted else 0,
            direction=Direction.OUTBOUND,
            payload_entropy=random.uniform(0.8, 0.95),  # Very high entropy (encrypted/compressed)
        )
    
    def _create_brute_force_packet(self) -> Packet:
        """Create a brute force attack packet"""
        target_port = random.choice(self.parameters["target_ports"])
        self.parameters["credentials_tried"] += 1
        
        credentials = [
            f"admin:admin{random.randint(1, 999)}",
            f"root:password{random.randint(1, 999)}",
            f"user:123456",
            f"administrator:qwerty",
            f"guest:guest",
        ]
        
        return Packet(
            packet_id=f"brute_{self.attack_id}_{self.packets_sent:06d}",
            source_id=self.source_id,
            destination_id=self.target_id,
            source_port=random.randint(49152, 65535),
            destination_port=target_port,
            protocol=Protocol.TCP,
            packet_type=PacketType.ATTACK,
            tcp_flags=TCPFlags(ack=True, psh=True),
            payload=f"LOGIN:{random.choice(credentials)}",
            payload_size=self.parameters["packet_size"],
            is_malicious=True,
            threat_score=0.7,
            direction=Direction.OUTBOUND,
            payload_entropy=random.uniform(0.4, 0.7),
        )
    
    def _create_sql_injection_packet(self) -> Packet:
        """Create an SQL injection attack packet"""
        sql_payload = random.choice(self.parameters["sql_patterns"])
        
        return Packet(
            packet_id=f"sql_{self.attack_id}_{self.packets_sent:06d}",
            source_id=self.source_id,
            destination_id=self.target_id,
            source_port=random.randint(49152, 65535),
            destination_port=80,  # Usually web servers
            protocol=Protocol.HTTP,
            packet_type=PacketType.ATTACK,
            payload=f"GET /login.php?user={sql_payload} HTTP/1.1",
            payload_size=self.parameters["payload_size"],
            is_malicious=True,
            threat_score=0.8,
            direction=Direction.OUTBOUND,
            payload_entropy=random.uniform(0.5, 0.8),
        )
    
    def _create_generic_attack_packet(self) -> Packet:
        """Create a generic attack packet"""
        return Packet.create_attack_packet(
            source=self.source_id,
            destination=self.target_id,
            attack_type=self.attack_type.value,
            threat_score=0.5 + (0.5 * self.intensity)
        )
    
    def _update_attack_state(self, time_delta: float):
        """Update attack state and damage"""
        # Calculate damage based on attack type and intensity
        base_damage = 0.0
        
        if self.attack_type == AttackType.DDOS:
            base_damage = 0.8 * self.intensity * time_delta / 60  # Damage per minute
            
        elif self.attack_type == AttackType.MALWARE_SPREAD:
            base_damage = 0.3 * self.intensity * time_delta / 60
            
        elif self.attack_type == AttackType.PORT_SCAN:
            base_damage = 0.1 * self.intensity * time_delta / 60
            
        elif self.attack_type == AttackType.BRUTE_FORCE:
            base_damage = 0.2 * self.intensity * time_delta / 60
            # Chance of success increases with attempts
            if self.parameters["credentials_tried"] > 100:
                success_chance = min(0.3, self.parameters["credentials_tried"] / 1000)
                if random.random() < success_chance:
                    base_damage += 0.5  # Successful login!
        
        self.damage_caused = min(100.0, self.damage_caused + base_damage)
        
        # Check if attack should stop
        if self.attack_type == AttackType.DDOS:
            attack_duration = (datetime.now() - self.start_time).total_seconds()
            if attack_duration > self.parameters["flood_duration"]:
                self.stop()
        
        # Random chance of being detected
        if not self.detected:
            detection_chance = 0.01 * self.intensity * time_delta
            if random.random() < detection_chance:
                self.detected = True
                self.detection_time = datetime.now()
    
    def stop(self):
        """Stop the attack"""
        self.is_active = False
        self.stopped = True
    
    def to_dict(self) -> Dict:
        """Convert attack to dictionary"""
        return {
            "id": self.attack_id,
            "type": self.attack_type.value,
            "source": self.source_id,
            "target": self.target_id,
            "intensity": self.intensity,
            "is_active": self.is_active,
            "detected": self.detected,
            "stopped": self.stopped,
            "start_time": self.start_time.isoformat(),
            "detection_time": self.detection_time.isoformat() if self.detection_time else None,
            "duration": (datetime.now() - self.start_time).total_seconds(),
            "packets_sent": self.packets_sent,
            "bytes_sent": self.bytes_sent,
            "damage_caused": self.damage_caused,
        }

class AttackGenerator:
    """Generates and manages cyber attacks"""
    
    def __init__(self, network: NetworkGraph):
        self.network = network
        self.attacks: Dict[str, Attack] = {}
        self.attack_counter = 0
        
        # Attack probabilities (chance per second)
        self.attack_probabilities = {
            AttackType.PORT_SCAN: 0.02,      # 2% chance per second
            AttackType.DDOS: 0.005,          # 0.5% chance
            AttackType.MALWARE_SPREAD: 0.01, # 1% chance
            AttackType.BRUTE_FORCE: 0.008,   # 0.8% chance
            AttackType.SQL_INJECTION: 0.003, # 0.3% chance
            AttackType.XSS: 0.002,           # 0.2% chance
            AttackType.CSRF: 0.002,          # 0.2% chance
            AttackType.ARP_SPOOFING: 0.001,  # 0.1% chance
            AttackType.ZERO_DAY: 0.0001,     # 0.01% chance (very rare)
        }  
        
        # Statistics
        self.stats = {
            "total_attacks": 0,
            "active_attacks": 0,
            "detected_attacks": 0,
            "stopped_attacks": 0,
            "total_damage": 0.0,
            "total_packets": 0,
            "total_bytes": 0,
        }
    
    def generate_random_attack(self, intensity: float = None) -> Optional[Attack]:
        """Generate a random attack"""
        if intensity is None:
            intensity = random.uniform(0.3, 0.9)
        
        # Select attack type based on probabilities
        attack_type = random.choices(
            list(self.attack_probabilities.keys()),
            weights=list(self.attack_probabilities.values())
        )[0]
        
        return self.generate_specific_attack(attack_type, intensity)
    
    def generate_specific_attack(self, attack_type, 
                                intensity: float = 0.7) -> Optional[Attack]:
        """Generate a specific type of attack"""
        attack_type = AttackType(attack_type) if isinstance(attack_type, str) else attack_type
        nodes = list(self.network.nodes.values())
        if len(nodes) < 2:
            return None
        
        # Select source (must be compromised or will become compromised)
        source = self._select_attack_source(nodes, attack_type)
        if not source:
            return None
        
        # Select target
        target = self._select_attack_target(nodes, source, attack_type)
        if not target:
            return None
        
        # Mark source as compromised
        source.is_compromised = True
        
        # Create attack
        attack_id = f"atk_{self.attack_counter:06d}"
        attack = Attack(
            attack_id=attack_id,
            attack_type=attack_type,
            source_id=source.id,
            target_id=target.id,
            intensity=intensity
        )
        
        self.attacks[attack_id] = attack
        self.attack_counter += 1
        
        # Update statistics
        self.stats["total_attacks"] += 1
        self.stats["active_attacks"] += 1
        
        print(f"⚔️  Attack launched: {attack_type} "
              f"from {source.name} to {target.name} "
              f"(intensity: {intensity:.2f})")
        
        return attack
    
    def _select_attack_source(self, nodes: List, attack_type: AttackType):
        """Select source node for attack"""
        # Prefer already compromised nodes
        compromised = [n for n in nodes if n.is_compromised]
        if compromised:
            return random.choice(compromised)
        
        # If no compromised nodes, select a vulnerable one
        vulnerable = [n for n in nodes if n.security_level < 50]
        if vulnerable:
            return random.choice(vulnerable)
        
        # Otherwise random node
        return random.choice(nodes)
    
    def _select_attack_target(self, nodes: List, source, attack_type: AttackType):
        """Select target node for attack"""
        # Remove source from potential targets
        potential_targets = [n for n in nodes if n.id != source.id]
        
        if attack_type == AttackType.DDOS:
            # DDoS targets valuable nodes
            valuable = [n for n in potential_targets if n.value_score >= 7]
            if valuable:
                return random.choice(valuable)
        
        elif attack_type == AttackType.SQL_INJECTION:
            # SQL injection targets servers with database/web services
            db_servers = [
                n for n in potential_targets 
                if any(service in ["http", "database", "web"] for service in n.services)
            ]
            if db_servers:
                return random.choice(db_servers)
        
        elif attack_type == AttackType.BRUTE_FORCE:
            # Brute force targets servers with remote access
            remote_servers = [
                n for n in potential_targets 
                if any(service in ["ssh", "rdp", "vnc", "telnet"] for service in n.services)
            ]
            if remote_servers:
                return random.choice(remote_servers)
        
        # Default: random target
        return random.choice(potential_targets) if potential_targets else None
    
    def update(self, time_delta: float = 1.0) -> List[Packet]:
        """Update all attacks and generate packets"""
        all_packets = []
        
        # Update existing attacks
        for attack in list(self.attacks.values()):
            if attack.is_active and not attack.stopped:
                packets = attack.generate_packets(time_delta)
                all_packets.extend(packets)
                
                # Update stats
                self.stats["total_packets"] += len(packets)
                self.stats["total_bytes"] += sum(p.payload_size for p in packets)
                
                # Update damage
                self.stats["total_damage"] = sum(a.damage_caused for a in self.attacks.values())
                
                # Check if attack should be auto-stopped
                if attack.detected and random.random() < 0.1 * time_delta:
                    attack.stop()
                    self.stats["stopped_attacks"] += 1
                    self.stats["active_attacks"] -= 1
        
        # Random chance to generate new attack
        for attack_type, probability in self.attack_probabilities.items():
            if random.random() < probability * time_delta:
                self.generate_specific_attack(attack_type)
        
        return all_packets
    
    def stop_attack(self, attack_id: str) -> bool:
        """Stop a specific attack"""
        if attack_id in self.attacks:
            attack = self.attacks[attack_id]
            if attack.is_active:
                attack.stop()
                self.stats["stopped_attacks"] += 1
                self.stats["active_attacks"] -= 1
                return True
        return False
    
    def stop_all_attacks(self):
        """Stop all active attacks"""
        for attack in self.attacks.values():
            if attack.is_active:
                attack.stop()
                self.stats["stopped_attacks"] += 1
        
        self.stats["active_attacks"] = 0
    
    def get_active_attacks(self) -> List[Dict]:
        """Get information about active attacks"""
        return [attack.to_dict() for attack in self.attacks.values() 
                if attack.is_active and not attack.stopped]
    
    def get_detected_attacks(self) -> List[Dict]:
        """Get detected attacks"""
        return [attack.to_dict() for attack in self.attacks.values() 
                if attack.detected]
    
    def get_stats(self) -> Dict:
        """Get attack statistics"""
        detected = len([a for a in self.attacks.values() if a.detected])
        self.stats["detected_attacks"] = detected
        
        return self.stats.copy()
    
    def clear(self):
        """Clear all attacks"""
        self.attacks.clear()
        self.attack_counter = 0
        self.stats = {
            "total_attacks": 0,
            "active_attacks": 0,
            "detected_attacks": 0,
            "stopped_attacks": 0,
            "total_damage": 0.0,
            "total_packets": 0,
            "total_bytes": 0,
        }