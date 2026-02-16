import sys
import os
from backend.api import SimulationState
from flask import current_app
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from simulation import NetworkGraph, NetworkNode, NetworkEdge, NodeType, OperatingSystem
from datetime import datetime
import uuid
import random

class SimulationService:
    def __init__(self):
        self.agent_actions = []
        self.honeypots = []
        self.attack_history = []
        self.metrics_history = []
        
    def get_network_status(self):
        """Get overall network status"""
        simulation = current_app.simulation_state
        compromised_count = sum(1 for node in simulation.network.nodes.values() if node.is_compromised)
        quarantined_count = sum(1 for node in simulation.network.nodes.values() if node.is_quarantined)
        
        return {
            'status': simulation.status,
            'total_nodes': len(simulation.network.nodes),
            'attack_stats': simulation.attack_generator.get_stats(),
            'active_attacks': simulation.attack_generator.get_active_attacks(),
            'detected_attacks': simulation.attack_generator.get_detected_attacks(),
            'quarantined_nodes': quarantined_count,
            'honeypots_deployed': len(self.honeypots),
            'compromised_nodes': compromised_count,
            'threat_level': self._calculate_threat_level(),
            'traffic stats': simulation.traffic_generator.get_traffic_stats(),
            'last_updated': datetime.now().isoformat()
        }
    
    def _calculate_threat_level(self):
        """Calculate current threat level"""
        if len(self.active_attacks) > 3:
            return 'High'
        elif len(self.active_attacks) > 1:
            return 'Medium'
        else:
            return 'Low'
    
    def inject_attack(self, attack_type, severity='Medium'):
        """Inject a new attack"""
        simulation = current_app.simulation_state
        attack = simulation.attack_generator.generate_specific_attack(attack_type, severity)
        
        self.attack_history.append(attack)
        
        # Add agent action
        self.agent_actions.append({
            'agent': f'Agent-{random.randint(1, 4):02d}',
            'action': f'Detected {attack_type} attack',
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'severity': severity
        })
        
        return attack
    
    def get_active_attacks(self):
        simulation = current_app.simulation_state
        return simulation.attack_generator.get_active_attacks()
    
    def get_agent_actions(self, limit=50):
        return self.agent_actions[-limit:]
    
    def deploy_honeypot(self, name, honeypot_type, ip=None, location=None):
        """Deploy a new honeypot"""
        simulation = current_app.simulation_state
        
        if not ip:
            ip = f"192.168.1.{random.randint(200, 250)}"
        
        honeypot = NetworkNode()
        honeypot.name = name
        honeypot.node_type = NodeType.HONEYPOT
        honeypot.ip_address = ip
        honeypot.os = OperatingSystem.LINUX
        honeypot.is_honeypot = True
        honeypot.security_level = 20  # Honeypots are intentionally vulnerable
        honeypot.value_score = 5  # Moderate value for scoring
        
        self.honeypots.append(honeypot.to_dict())
        
        return honeypot
    
    def trigger_honeypot(self, honeypot_id, data):
        """Record a honeypot trigger"""
        for honeypot in self.honeypots:
            if honeypot['id'] == honeypot_id:
                honeypot['triggers'] += 1
                attack_info = {
                    'timestamp': datetime.now().isoformat(),
                    'source': data.get('source', 'Unknown'),
                    'attack_type': data.get('attack_type', 'Unknown')
                }
                honeypot['attacks_caught'].append(attack_info)
                return {'success': True, 'honeypot': honeypot}
        return {'success': False, 'error': 'Honeypot not found'}
    
    def get_all_honeypots(self):
        return self.honeypots
    
    def get_honeypot_strategy(self):
        return {
            'strategy': 'Deceptive Layer',
            'deployment': 'Strategic placement at network perimeter',
            'types': ['Low Interaction', 'Medium Interaction', 'High Interaction'],
            'current_focus': 'Catching reconnaissance attacks'
        }
    
    def control_simulation(self, action, data=None):
        """Control simulation state"""
        simulation = current_app.simulation_state
        if action == 'start':
            simulation.is_running = True
            simulation.start_time = datetime.now()
        elif action == 'pause':
            simulation.is_running = False
            simulation.start_time = None
        elif action == 'reset':
            simulation.is_running = False
            current_app.simulation_state = SimulationState()
            self.agent_actions = []
            self.honeypots = []
            self.attack_history = []
            self.metrics_history = []
        
        return {
            'action': action,
            'state': 'Running' if simulation.is_running else 'Paused',
            'timestamp': datetime.now().isoformat()
        }
    
    def get_simulation_state(self):
        simulation = current_app.simulation_state
        return {
            'state': 'Running' if simulation.is_running else 'Paused',
            'timestamp': datetime.now().isoformat()
        }
    
    
    def get_all_agents(self):
        """Get all agents in the network"""
        simulation = current_app.simulation_state
        agents = []
        for node in simulation.network.nodes.values():
            if node.node_type.value == 'AGENT' if hasattr(node.node_type, 'value') else False:
                agents.append({
                    'id': node.id,
                    'name': node.name,
                    'ip_address': node.ip_address,
                    'os': node.os.value if hasattr(node.os, 'value') else str(node.os),
                    'security_level': node.security_level,
                    'is_compromised': node.is_compromised,
                    'is_quarantined': node.is_quarantined
                })
        return agents
    
    def get_agent_actions(self, limit=50):
        """Get recent agent actions"""
        return self.agent_actions[-limit:]
    
    def get_agent(self, agent_id):
        """Get specific agent by ID"""
        simulation = current_app.simulation_state
        for node in simulation.network.nodes.values():
            if node.id == agent_id and (node.node_type.value == 'AGENT' if hasattr(node.node_type, 'value') else False):
                return {
                    'id': node.id,
                    'name': node.name,
                    'ip_address': node.ip_address,
                    'os': node.os.value if hasattr(node.os, 'value') else str(node.os),
                    'security_level': node.security_level,
                    'is_compromised': node.is_compromised,
                    'is_quarantined': node.is_quarantined
                }
        return None
    
    def get_agent_decisions(self, agent_id):
        """Get decision history for a specific agent"""
        decisions = []
        for action in self.agent_actions:
            if action['agent'] == f'Agent-{agent_id[-2:]}':
                decisions.append(action)
        return decisions