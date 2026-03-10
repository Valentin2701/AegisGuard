import networkx as nx
from typing import Dict, List, Optional, Tuple, Any
import random
import string

from backend.simulation.config.network_config import NetworkConfig
from .network_node import NetworkNode, NodeType, OperatingSystem
from .network_edge import NetworkEdge, Protocol

class NetworkGraph:
    def __init__(self):
        self.graph = nx.Graph()
        self.nodes: Dict[str, NetworkNode] = {}
        self.edges: Dict[str, NetworkEdge] = {}
        self.edge_counter = 0
    
    def add_node(self, node: NetworkNode) -> None:
        self.nodes[node.id] = node
        
        # Add node attributes without the 'id' field
        node_data = node.to_dict()
        # Remove 'id' from node data since node ID is the key in NetworkX
        node_data.pop('id', None)
        
        self.graph.add_node(node.id, **node_data)
    
    def add_edge(self, edge: NetworkEdge) -> None:
        self.edges[edge.id] = edge
        
        # Get edge data without the 'id' field
        edge_data = edge.to_dict()
        # Remove fields that conflict with NetworkX or are redundant
        edge_data.pop('id', None)
        edge_data.pop('source', None)
        edge_data.pop('target', None)
        
        # Add edge with attributes
        self.graph.add_edge(edge.source_id, edge.target_id, **edge_data)
        
        # Store the edge ID separately as an attribute
        self.graph[edge.source_id][edge.target_id]['edge_id'] = edge.id
    
    def remove_node(self, node_id: str) -> bool:
        if node_id in self.nodes:
            del self.nodes[node_id]
            self.graph.remove_node(node_id)
            edge_ids_to_remove = [
                eid for eid, edge in self.edges.items()
                if edge.source_id == node_id or edge.target_id == node_id
            ]
            for eid in edge_ids_to_remove:
                del self.edges[eid]
            return True
        return False
    
    def get_node(self, node_id: str) -> Optional[NetworkNode]:
        return self.nodes.get(node_id)
    
    def get_edge(self, source_id: str, target_id: str) -> Optional[NetworkEdge]:
        for edge in self.edges.values():
            if (edge.source_id == source_id and edge.target_id == target_id) or \
               (edge.source_id == target_id and edge.target_id == source_id):
                return edge
        
        if self.graph.has_edge(source_id, target_id):
            edge_data = self.graph[source_id][target_id]
            edge_id = edge_data.get('edge_id', f"{source_id}_{target_id}")
            
            return NetworkEdge(
                id=edge_id,
                source_id=source_id,
                target_id=target_id,
                bandwidth=edge_data.get('bandwidth', 100),
                latency=edge_data.get('latency', 10),
                supported_protocols=[Protocol(p) for p in edge_data.get('supported_protocols', ['tcp'])],
                current_protocol=Protocol(edge_data['current_protocol']) if edge_data.get('current_protocol') else None,
                encryption_level=edge_data.get('encryption_level', 0),
                is_monitored=edge_data.get('is_monitored', False),
                traffic_volume=edge_data.get('traffic_volume', 0),
                packet_count=edge_data.get('packet_count', 0),
                error_rate=edge_data.get('error_rate', 0)
            )
        return None
    
    def get_edge_by_id(self, edge_id: str) -> Optional[NetworkEdge]:
        return self.edges.get(edge_id)
    
    def update_edge_attributes(self, edge_id: str, **kwargs) -> bool:
        if edge_id in self.edges:
            edge = self.edges[edge_id]
            
            # Update the NetworkEdge object
            for key, value in kwargs.items():
                if hasattr(edge, key):
                    setattr(edge, key, value)
            
            # Also update the NetworkX graph
            if self.graph.has_edge(edge.source_id, edge.target_id):
                for key, value in kwargs.items():
                    if key not in ['id', 'source_id', 'target_id']:
                        self.graph[edge.source_id][edge.target_id][key] = value
            
            return True
        return False
    
    def generate_random_node_id(self) -> str:
        while True:
            node_id = f"node_{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}"
            if node_id not in self.nodes:
                return node_id
    
    def generate_random_edge_id(self) -> str:
        self.edge_counter += 1
        return f"edge_{self.edge_counter:06d}"
    
    def create_small_office_network(self) -> None:
        # Clear existing network
        self.graph.clear()
        self.nodes.clear()
        self.edges.clear()
        self.edge_counter = 0
        
        # Create nodes
        nodes_data = [
            # Core infrastructure
            ("router_1", "Main Router", NodeType.ROUTER, OperatingSystem.CUSTOM, "192.168.1.1"),
            ("switch_1", "Core Switch", NodeType.SWITCH, OperatingSystem.CUSTOM, "192.168.1.2"),
            ("firewall_1", "Firewall", NodeType.FIREWALL, OperatingSystem.LINUX, "192.168.1.3"),
            
            # Servers
            ("web_server", "Web Server", NodeType.SERVER, OperatingSystem.LINUX, "192.168.1.10"),
            ("file_server", "File Server", NodeType.SERVER, OperatingSystem.LINUX, "192.168.1.11"),
            ("db_server", "Database Server", NodeType.SERVER, OperatingSystem.LINUX, "192.168.1.12"),
            
            # Client machines
            ("client_1", "CEO Laptop", NodeType.CLIENT, OperatingSystem.WINDOWS, "192.168.1.100"),
            ("client_2", "IT Admin", NodeType.CLIENT, OperatingSystem.LINUX, "192.168.1.101"),
            ("client_3", "Sales PC", NodeType.CLIENT, OperatingSystem.WINDOWS, "192.168.1.102"),
        ]
        
        for node_id, name, node_type, os, ip in nodes_data:
            node = NetworkNode(
                id=node_id,
                name=name,
                node_type=node_type,
                os=os,
                ip_address=ip,
                mac_address=f"00:1A:2B:3C:4D:{random.randint(10,99):02d}",
                security_level=random.randint(50, 90),
                services=self._get_default_services(node_type),
                value_score=self._get_value_score(node_type, name)
            )
            self.add_node(node)
        
        # Create edges (connections)
        connections = [
            ("router_1", "switch_1"),
            ("switch_1", "firewall_1"),
            ("firewall_1", "web_server"),
            ("firewall_1", "file_server"),
            ("firewall_1", "db_server"),
            ("switch_1", "client_1"),
            ("switch_1", "client_2"),
            ("switch_1", "client_3"),
        ]
        
        for source_id, target_id in connections:
            edge = NetworkEdge(
                id=self.generate_random_edge_id(),
                source_id=source_id,
                target_id=target_id,
                bandwidth=random.choice([100, 1000]),  # 100Mbps or 1Gbps
                latency=random.uniform(1, 10),  # 1-10ms
                supported_protocols=[Protocol.TCP, Protocol.HTTP, Protocol.HTTPS, Protocol.SSH],
                current_protocol=random.choice([Protocol.HTTPS, Protocol.SSH]),
                encryption_level=random.randint(70, 95)
            )
            self.add_edge(edge)
    
    def _get_default_services(self, node_type: NodeType) -> List[str]:
        defaults = {
            NodeType.SERVER: ["http", "ssh", "database"],
            NodeType.CLIENT: ["browser", "email", "office"],
            NodeType.ROUTER: ["routing", "nat", "dhcp"],
            NodeType.FIREWALL: ["firewall", "ids", "vpn"],
            NodeType.SWITCH: ["switching", "vlan"],
            NodeType.HONEYPOT: ["http", "ssh", "ftp", "telnet"]
        }
        return defaults.get(node_type, [])
    
    def _get_value_score(self, node_type: NodeType, name: str) -> int:
        if "CEO" in name or "Database" in name:
            return 10
        elif node_type == NodeType.SERVER:
            return 8
        elif node_type == NodeType.FIREWALL or node_type == NodeType.ROUTER:
            return 7
        elif "Admin" in name:
            return 6
        else:
            return random.randint(3, 5)
    
    def to_dict(self) -> Dict:
        return {
            "nodes": {nid: node.to_dict() for nid, node in self.nodes.items()},
            "edges": {eid: edge.to_dict() for eid, edge in self.edges.items()},
            "graph_metrics": {
                "node_count": len(self.nodes),
                "edge_count": len(self.edges),
                "density": nx.density(self.graph) if len(self.nodes) > 1 else 0,
                "is_connected": nx.is_connected(self.graph) if len(self.nodes) > 0 else False
            }
        }
    
    def visualize(self, filename: str = "network.png") -> None:
        try:
            import matplotlib.pyplot as plt
            
            plt.figure(figsize=(12, 8))
            
            # Position nodes using spring layout
            pos = nx.spring_layout(self.graph, seed=42)
            
            # Draw nodes with different colors based on type
            node_colors = []
            for node_id in self.graph.nodes():
                node_type = self.nodes[node_id].node_type
                if node_type == NodeType.SERVER:
                    node_colors.append('red')
                elif node_type == NodeType.CLIENT:
                    node_colors.append('green')
                elif node_type == NodeType.ROUTER:
                    node_colors.append('blue')
                elif node_type == NodeType.FIREWALL:
                    node_colors.append('orange')
                elif node_type == NodeType.SWITCH:
                    node_colors.append('purple')
                else:
                    node_colors.append('gray')
            
            # Draw compromised nodes with a different shape
            compromised_nodes = [nid for nid, node in self.nodes.items() if node.is_compromised]
            normal_nodes = [nid for nid in self.graph.nodes() if nid not in compromised_nodes]
            
            # Draw normal nodes
            nx.draw_networkx_nodes(
                self.graph, pos, 
                nodelist=normal_nodes,
                node_color=[node_colors[list(self.graph.nodes()).index(nid)] for nid in normal_nodes],
                node_size=500
            )
            
            # Draw compromised nodes with X marker
            if compromised_nodes:
                nx.draw_networkx_nodes(
                    self.graph, pos,
                    nodelist=compromised_nodes,
                    node_color='black',
                    node_size=700,
                    node_shape='X'
                )
            
            # Draw edges
            nx.draw_networkx_edges(self.graph, pos, alpha=0.5, width=2)
            
            # Draw labels
            nx.draw_networkx_labels(self.graph, pos, font_size=10)
            
            # Draw edge labels (bandwidth)
            edge_labels = {}
            for (u, v) in self.graph.edges():
                if 'bandwidth' in self.graph[u][v]:
                    edge_labels[(u, v)] = f"{self.graph[u][v]['bandwidth']}Mbps"
            
            nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels, font_size=8)
            
            plt.title("Network Topology")
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(filename, dpi=300)
            plt.close()
            print(f"Visualization saved to {filename}")
            
        except ImportError:
            print("Matplotlib not installed. Install with: pip install matplotlib")
        except Exception as e:
            print(f"Visualization error: {e}")
    def create_network_from_config(self, preset_name: str = "small_office"):
        """Create network from configuration preset"""
        from .config.network_config import NetworkConfig
    
        # Clear existing network
        self.graph.clear()
        self.nodes.clear()
        self.edges.clear()
        self.edge_counter = 0
    
        # Get configuration
        preset = NetworkConfig.get_topology_preset(preset_name)
        if not preset:
            print(f"⚠️  Preset '{preset_name}' not found, using small_office")
            preset = NetworkConfig.get_topology_preset("small_office")
    
        node_counts = preset["node_counts"]
        ip_range = preset["ip_range"]
    
        print(f"📊 Creating {preset_name} network: {preset['description']}")
    
        # Create all nodes
        node_id_counter = 0
    
        for node_type, count in node_counts.items():
            template = NetworkConfig.get_node_template(node_type)
            if not template:
                print(f"⚠️  Template not found for node type '{node_type}'")
                continue
            
            for i in range(count):
                node_id = f"{node_type.value}_{node_id_counter}"
                node_id_counter += 1
            
                # Generate IP based on node type and index
                if ip_range == "192.168.1.0/24":
                    ip_suffix = node_id_counter + 10  # Start from .11
                    ip_address = f"192.168.1.{ip_suffix}"
                elif ip_range == "10.0.0.0/16":
                    subnet = node_id_counter // 256
                    host = node_id_counter % 256
                    ip_address = f"10.0.{subnet}.{host}"
                elif ip_range == "172.16.0.0/12":
                    subnet = node_id_counter // 256
                    host = node_id_counter % 256
                    ip_address = f"172.16.{subnet}.{host}"
                elif ip_range == "10.10.0.0/24":
                    ip_address = f"10.10.0.{node_id_counter + 10}"
                else:
                    ip_address = f"10.0.0.{node_id_counter}"
            
                # Create node
                node = NetworkNode(
                    id=node_id,
                    name=f"{node_type.value.title()} {i+1}",
                    node_type=node_type,
                    os=template.os,
                    ip_address=ip_address,
                    mac_address=f"00:1A:2B:3C:4D:{node_id_counter:02d}",
                    security_level=template.generate_security_level(),
                    services=template.default_services.copy(),
                    value_score=template.generate_value_score()
                )
            
                self.add_node(node)
    
        # Create basic connectivity (simplified)
        # In a real implementation, you'd create more sophisticated topologies
        node_ids = list(self.nodes.keys())
    
        # Create a hierarchical structure
        # 1. Connect routers together (if multiple routers)
        routers = [nid for nid, node in self.nodes.items() if node.node_type == NodeType.ROUTER]
        if len(routers) > 1:
            for i in range(len(routers) - 1):
                edge = NetworkEdge(
                    id=self.generate_random_edge_id(),
                    source_id=routers[i],
                    target_id=routers[i + 1],
                    bandwidth=10000,  # 10 Gbps
                    latency=1.0,
                    supported_protocols=[Protocol.TCP, Protocol.UDP, Protocol.ICMP],
                    current_protocol=Protocol.TCP,
                    encryption_level=95
                )
                self.add_edge(edge)
    
        # 2. Connect switches to routers
        switches = [nid for nid, node in self.nodes.items() if node.node_type == NodeType.SWITCH]
        for switch in switches:
            if routers:
                router = random.choice(routers)
                edge = NetworkEdge(
                    id=self.generate_random_edge_id(),
                    source_id=switch,
                    target_id=router,
                    bandwidth=10000,
                    latency=2.0,
                    supported_protocols=[Protocol.TCP, Protocol.UDP],
                    current_protocol=Protocol.TCP,
                    encryption_level=90
                )
                self.add_edge(edge)
    
        # 3. Connect other nodes to switches
        for node_id, node in self.nodes.items():
            if node.node_type not in [NodeType.ROUTER, NodeType.SWITCH]:
                if switches:
                    switch = random.choice(switches)
                    edge = NetworkEdge(
                        id=self.generate_random_edge_id(),
                        source_id=node_id,
                        target_id=switch,
                        bandwidth=template.typical_bandwidth if (template := NetworkConfig.get_node_template(node.node_type)) else 100,
                        latency=5.0,
                        supported_protocols=[Protocol.TCP, Protocol.HTTP, Protocol.HTTPS],
                        current_protocol=Protocol.HTTPS,
                        encryption_level=random.randint(70, 95)
                    )
                    self.add_edge(edge)
    
        print(f"✅ Created network: {len(self.nodes)} nodes, {len(self.edges)} edges")
        return self