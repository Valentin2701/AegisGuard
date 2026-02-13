import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from network_graph import NetworkGraph
from datetime import datetime
import uuid

class NetworkService:
    def __init__(self):
        self.network = NetworkGraph()
        self.network.create_small_office_network()
        self.quarantine_logs = []
    
    def get_all_nodes(self):
        """Get all nodes in the network"""
        nodes = []
        for node_id, node in self.network.nodes.items():
            nodes.append({
                'id': node_id,
                'name': node.name,
                'type': node.node_type.value if hasattr(node.node_type, 'value') else str(node.node_type),
                'status': 'Compromised' if node.is_compromised else 'Quarantined' if node.is_quarantined else 'Healthy',
                'ip': node.ip_address,
                'os': node.os.value if hasattr(node.os, 'value') else str(node.os),
                'threat_score': node.threat_score if hasattr(node, 'threat_score') else 0,
                'connections': self._get_node_connections(node_id),
                'last_seen': datetime.now().isoformat(),
                'is_compromised': node.is_compromised,
                'is_quarantined': node.is_quarantined,
                'is_honeypot': node.node_type.value == 'HONEYPOT' if hasattr(node.node_type, 'value') else False
            })
        return nodes
    
    def _get_node_connections(self, node_id):
        """Get connections for a specific node"""
        connections = []
        for edge in self.network.edges:
            if edge[0] == node_id:
                connections.append(edge[1])
            elif edge[1] == node_id:
                connections.append(edge[0])
        return connections[:5]  # Limit to 5 connections
    
    def get_node(self, node_id):
        """Get specific node by ID"""
        nodes = self.get_all_nodes()
        for node in nodes:
            if node['id'] == node_id:
                return node
        return None
    
    def get_nodes_by_status(self, status):
        """Get nodes by status"""
        nodes = self.get_all_nodes()
        if status.lower() == 'healthy':
            return [n for n in nodes if not n['is_compromised'] and not n['is_quarantined']]
        elif status.lower() == 'compromised':
            return [n for n in nodes if n['is_compromised']]
        elif status.lower() == 'quarantined':
            return [n for n in nodes if n['is_quarantined']]
        elif status.lower() == 'honeypot':
            return [n for n in nodes if n['is_honeypot']]
        else:
            return []
    
    def get_quarantined_nodes(self):
        """Get all quarantined nodes"""
        return self.get_nodes_by_status('quarantined')
    
    def quarantine_node(self, node_id, reason):
        """Quarantine a specific node"""
        if node_id in self.network.nodes:
            self.network.nodes[node_id].is_quarantined = True
            self.network.nodes[node_id].is_compromised = False
            
            log_entry = {
                'id': str(uuid.uuid4())[:8],
                'node_id': node_id,
                'node_name': self.network.nodes[node_id].name,
                'action': 'quarantine',
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            }
            self.quarantine_logs.append(log_entry)
            
            return log_entry
        return None
    
    def release_node(self, node_id):
        """Release a node from quarantine"""
        if node_id in self.network.nodes and self.network.nodes[node_id].is_quarantined:
            self.network.nodes[node_id].is_quarantined = False
            
            log_entry = {
                'id': str(uuid.uuid4())[:8],
                'node_id': node_id,
                'node_name': self.network.nodes[node_id].name,
                'action': 'release',
                'reason': 'Security clearance',
                'timestamp': datetime.now().isoformat()
            }
            self.quarantine_logs.append(log_entry)
            
            return log_entry
        return None
    
    def get_quarantine_logs(self):
        return self.quarantine_logs[-50:]  # Last 50 logs
    
    def get_network_topology(self):
        """Get complete network topology"""
        return {
            'nodes': self.get_all_nodes(),
            'edges': [{'source': e[0], 'target': e[1]} for e in self.network.edges]
        }