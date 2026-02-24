import sys
import os
from flask import current_app
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import datetime
import uuid

class NetworkService:
    def __init__(self):
        self.quarantine_logs = []

    def get_network_status(self):
        simulation = current_app.simulation_state
        total_nodes = len(simulation.network.nodes)
        compromised_nodes = len([n for n in simulation.network.nodes.values() if n.is_compromised])
        quarantined_nodes = len([n for n in simulation.network.nodes.values() if n.is_quarantined])
        attacks = simulation.attack_generator.get_active_attacks()
        threat_level = sum([a.get('intensity', 0) for a in attacks]) / (len(attacks) + 1)
        
        return {
            'total_nodes': total_nodes,
            'active_attacks': len(attacks),
            'compromised_nodes': compromised_nodes,
            'quarantined_nodes': quarantined_nodes,
            'honeypots_deployed': len([n for n in simulation.network.nodes.values() if n.node_type.value == 'HONEYPOT' and n.is_honeypot]),
            'threat_level': threat_level,
            'total_traffic': simulation.traffic_generator.get_traffic_stats().get('total_bytes', 0),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_all_nodes(self):
        """Get all nodes in the network"""
        simulation = current_app.simulation_state
        nodes = []
        for node_id, node in simulation.network.nodes.items():
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
        simulation = current_app.simulation_state
        connections = []
        for edge in simulation.network.edges:
            if edge[0] == node_id:
                connections.append(edge[1])
            elif edge[1] == node_id:
                connections.append(edge[0])
        return connections[:5]  # Limit to 5 connections
    
    def get_node(self, node_id):
        """Get specific node by ID"""
        simulation = current_app.simulation_state
        return simulation.network.get_node(node_id).to_dict() if node_id in simulation.network.nodes else None
    
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
        
    def get_all_edges(self):
        simulation = current_app.simulation_state
        return [e.to_dict() for e in simulation.network.edges.values()]
    
    def get_all_connections(self):
        simulation = current_app.simulation_state
        return [c.to_dict() for c in simulation.traffic_generator.connections.values()]
    
    def get_quarantined_nodes(self):
        """Get all quarantined nodes"""
        return self.get_nodes_by_status('quarantined')
    
    def quarantine_node(self, node_id, reason):
        """Quarantine a specific node"""
        simulation = current_app.simulation_state
        if node_id in simulation.network.nodes:
            simulation.network.nodes[node_id].is_quarantined = True
            simulation.network.nodes[node_id].is_compromised = False
            
            log_entry = {
                'id': str(uuid.uuid4())[:8],
                'node_id': node_id,
                'node_name': simulation.network.nodes[node_id].name,
                'action': 'quarantine',
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            }
            self.quarantine_logs.append(log_entry)
            
            return log_entry
        return None
    
    def release_node(self, node_id):
        """Release a node from quarantine"""
        simulation = current_app.simulation_state
        if node_id in simulation.network.nodes and simulation.network.nodes[node_id].is_quarantined:
            simulation.network.nodes[node_id].is_quarantined = False
            
            log_entry = {
                'id': str(uuid.uuid4())[:8],
                'node_id': node_id,
                'node_name': simulation.network.nodes[node_id].name,
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
        simulation = current_app.simulation_state
        return {
            'nodes': self.get_all_nodes(),
            'edges': [{'source': e[0], 'target': e[1]} for e in simulation.network.edges]
        }