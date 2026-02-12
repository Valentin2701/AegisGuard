import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from simulation import NetworkGraph, NetworkNode, NetworkEdge, NodeType, OperatingSystem
from datetime import datetime
import uuid
import random

class SimulationService:
    def __init__(self):
        self.network = NetworkGraph()
        self.network.create_small_office_network()
        self.simulation_state = 'stopped'
        self.active_attacks = []
        self.agent_actions = []
        self.honeypots = []
        self.attack_history = []
        self.metrics_history = []
        
    def get_network_status(self):
        """Get overall network status"""
        compromised_count = sum(1 for node in self.network.nodes.values() if node.is_compromised)
        quarantined_count = sum(1 for node in self.network.nodes.values() if node.is_quarantined)
        
        return {
            'status': self.simulation_state,
            'total_nodes': len(self.network.nodes),
            'active_attacks': len(self.active_attacks),
            'quarantined_nodes': quarantined_count,
            'honeypots_deployed': len(self.honeypots),
            'threat_level': self._calculate_threat_level(),
            'total_traffic': random.uniform(30, 60),
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
    
    def inject_attack(self, attack_type, target, severity='Medium', source='Unknown'):
        """Inject a new attack"""
        attack_id = str(uuid.uuid4())[:8]
        attack = {
            'id': attack_id,
            'type': attack_type,
            'source': source,
            'target': target,
            'severity': severity,
            'status': 'Active',
            'started': datetime.now().strftime('%H:%M:%S'),
            'timestamp': datetime.now().isoformat(),
            'agent_action': 'Detecting'
        }
        
        self.active_attacks.append(attack)
        self.attack_history.append(attack)
        
        # Add agent action
        self.agent_actions.append({
            'agent': f'Agent-{random.randint(1, 4):02d}',
            'action': f'Detected {attack_type} attack on {target}',
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'severity': severity
        })
        
        return attack
    
    def get_active_attacks(self):
        return self.active_attacks
    
    def get_agent_actions(self, limit=50):
        return self.agent_actions[-limit:]
    
    def deploy_honeypot(self, name, honeypot_type, ip=None, location=None):
        """Deploy a new honeypot"""
        honeypot_id = str(uuid.uuid4())[:8]
        
        if not ip:
            ip = f"192.168.1.{random.randint(200, 250)}"
        
        honeypot = {
            'id': honeypot_id,
            'name': name,
            'type': honeypot_type,
            'ip': ip,
            'location': location or 'Perimeter',
            'status': 'Active',
            'deployed_at': datetime.now().isoformat(),
            'triggers': 0,
            'attacks_caught': []
        }
        
        self.honeypots.append(honeypot)
        
        # Add node to network
        node_id = f"honeypot-{honeypot_id}"
        self.network.add_node(
            node_id,
            name,
            NodeType.HONEYPOT,
            ip,
            OperatingSystem.LINUX
        )
        
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
        if action == 'start':
            self.simulation_state = 'running'
        elif action == 'pause':
            self.simulation_state = 'paused'
        elif action == 'reset':
            self.simulation_state = 'stopped'
            self.network = NetworkGraph()
            self.network.create_small_office_network()
            self.active_attacks = []
            self.honeypots = []
        
        return {
            'action': action,
            'state': self.simulation_state,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_simulation_state(self):
        return {
            'state': self.simulation_state,
            'timestamp': datetime.now().isoformat()
        }