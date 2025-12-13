import networkx as nx
from typing import Dict, List, Optional, Tuple
import random
import string
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
        self.graph.add_node(node.id, **node.to_dict())
    
    def add_edge(self, edge: NetworkEdge) -> None:
        self.edges[edge.id] = edge
        self.graph.add_edge(
            edge.source_id, 
            edge.target_id, 
            id=edge.id,
            **edge.to_dict()
        )
    
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
        return None
    
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
        
        # Create nodes
        nodes_data = [
            # Core infrastructure
            ("router_1", "Main Router", NodeType.ROUTER, OperatingSystem.CUSTOM, "192.168.1.1"),
            ("switch_1", "Core Switch", NodeType.SWITCH, OperatingSystem.CUSTOM, "192.168.1.2"),
            ("firewall_1", "Firewall", NodeType.FIREWALL, OperatingSystem.LINUX, "192.168.1.3"),
            
            # Servers
            ("web_server", "Web Server", NodeType.SERVER, OperatingSystem.LINUX, "192.168.1.10"),
            ("file_server", "File Server", NodeType.SERVER, NodeType.SERVER, "192.168.1.11"),
            ("db_server", "Database Server", NodeType.SERVER, OperatingSystem.LINUX, "192.168.1.12"),
            
            # Client machines
            ("client_1", "CEO Laptop", NodeType.CLIENT, OperatingSystem.WINDOWS, "192.168.1.100"),
            ("client_2", "IT Admin", NodeType.CLIENT, OperatingSystem.LINUX, "192.168.1.101"),
            ("client_3", "Sales PC", NodeType.CLIENT, OperatingSystem.WINDOWS, "192.168.1.102"),
            ("client_4", "HR PC", NodeType.CLIENT, OperatingSystem.MACOS, "192.168.1.103"),
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
            ("switch_1", "client_4"),
        ]
        
        for source_id, target_id in connections:
            edge = NetworkEdge(
                id=self.generate_random_edge_id(),
                source_id=source_id,
                target_id=target_id,
                bandwidth=random.choice([100, 1000, 10000]),  # 100Mbps, 1Gbps, 10Gbps
                latency=random.uniform(1, 20),  # 1-20ms
                supported_protocols=[Protocol.TCP, Protocol.HTTP, Protocol.HTTPS, Protocol.SSH],
                current_protocol=Protocol.HTTPS,
                encryption_level=random.randint(70, 95)
            )
            self.add_edge(edge)
    
    def _get_default_services(self, node_type: NodeType) -> List[str]:
        """Get default services for a node type"""
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
        """Get importance score for a node"""
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
        """Convert entire network to dictionary"""
        return {
            "nodes": {nid: node.to_dict() for nid, node in self.nodes.items()},
            "edges": {eid: edge.to_dict() for eid, edge in self.edges.items()},
            "graph_metrics": {
                "node_count": len(self.nodes),
                "edge_count": len(self.edges),
                "density": nx.density(self.graph),
                "is_connected": nx.is_connected(self.graph)
            }
        }
    
    def visualize(self, filename: str = "network.png") -> None:
        """Create a simple visualization of the network"""
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
            
            nx.draw_networkx_nodes(self.graph, pos, node_color=node_colors, node_size=500)
            nx.draw_networkx_edges(self.graph, pos, alpha=0.5)
            nx.draw_networkx_labels(self.graph, pos, font_size=10)
            
            plt.title("Network Topology")
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(filename, dpi=300)
            plt.close()
            print(f"Visualization saved to {filename}")
            
        except ImportError:
            print("Matplotlib not installed. Install with: pip install matplotlib")