import sys
import os
from backend.api import SimulationState
from flask import current_app
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from simulation import NetworkGraph, NetworkNode, NetworkEdge, NodeType, OperatingSystem
from datetime import datetime, timedelta
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
    
    def _calculate_threat_level(self, active_attacks=None):
        """Calculate current threat level"""
        if active_attacks is None:
            active_attacks = self.get_active_attacks()
        if len(active_attacks) > 3:
            return 'High'
        elif len(active_attacks) > 1:
            return 'Medium'
        else:
            return 'Low'
        
    def get_attack(self, attack_id):
        """Get specific attack by ID"""
        simulation = current_app.simulation_state
        for attack in simulation.attack_generator.get_active_attacks():
            if attack['id'] == attack_id:
                return attack
        return None
    
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
    
    def get_attack_history(self, limit=100):
        return self.attack_history[-limit:]
    
    
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

        simulation.network.add_node(honeypot)
        
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
    
    def update_honeypot_strategy(self, strategy_data):
        # In a real implementation, this would update the strategy based on input data
        return {
            'strategy': strategy_data.get('strategy', 'Deceptive Layer'),
            'deployment': strategy_data.get('deployment', 'Strategic placement at network perimeter'),
            'types': strategy_data.get('types', ['Low Interaction', 'Medium Interaction', 'High Interaction']),
            'current_focus': strategy_data.get('current_focus', 'Catching reconnaissance attacks')
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
            'state': simulation,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_simulation_config(self):
        return {
            'network_size': len(current_app.simulation_state.network.nodes),
            'attack_frequency': 'Variable',
            'honeypot_count': len(self.honeypots),
            'traffic_pattern': 'Mixed',
            'timestamp': datetime.now().isoformat()
        }
    
    def update_simulation_config(self, config_data):
        # In a real implementation, this would update the simulation configuration based on input data
        return {
            'network_size': config_data.get('network_size', len(current_app.simulation_state.network.nodes)),
            'attack_frequency': config_data.get('attack_frequency', 'Variable'),
            'honeypot_count': config_data.get('honeypot_count', len(self.honeypots)),
            'traffic_pattern': config_data.get('traffic_pattern', 'Mixed'),
        }
    
    def seed_simulation(self, seed_data):
        """Seed simulation with specific parameters"""
        # In a real implementation, this would set up the simulation based on the provided seed data
        return {
            'seed': seed_data,
            'message': 'Simulation seeded with provided parameters',
            'timestamp': datetime.now().isoformat()
        }
    
    def get_current_metrics(self):
        simulation = current_app.simulation_state
        metrics = {
            'compromised_nodes': sum(1 for node in simulation.network.nodes.values() if node.is_compromised),
            'quarantined_nodes': sum(1 for node in simulation.network.nodes.values() if node.is_quarantined),
            'active_attacks': len(simulation.attack_generator.get_active_attacks()),
            'detected_attacks': len(simulation.attack_generator.get_detected_attacks()),
            'honeypots_deployed': len(self.honeypots),
            'traffic_metrics': simulation.traffic_generator.get_traffic_stats(),
            'attack_metrics': simulation.attack_generator.get_stats(),
            'threat_level': self._calculate_threat_level(),
            'timestamp': datetime.now().isoformat()
        }
        self.metrics_history.append(metrics)
        return metrics
    
    def get_metrics_history(self, timeframe='1h'):
        """Get historical metrics based on timeframe"""
        now = datetime.now()
        if timeframe.endswith('h'):
            hours = int(timeframe[:-1])
            cutoff = now - timedelta(hours=hours)
        elif timeframe.endswith('d'):
            days = int(timeframe[:-1])
            cutoff = now - timedelta(days=days)
        else:
            cutoff = now - timedelta(hours=1)  # Default to last hour
        
        return [m for m in self.metrics_history if datetime.fromisoformat(m['timestamp']) >= cutoff]
    
    def get_traffic_metrics(self):
        simulation = current_app.simulation_state
        return simulation.traffic_generator.get_traffic_stats()
    
    def get_threat_metrics(self):
        simulation = current_app.simulation_state
        return {
            'threat_level': self._calculate_threat_level(),
            'active_attacks': len(simulation.attack_generator.get_active_attacks()),
            'detected_attacks': len(simulation.attack_generator.get_detected_attacks())
        }
    
    def get_performance_metrics(self):
        simulation = current_app.simulation_state
        return {
            'memory_usage': simulation.traffic_generator.get_traffic_stats().get('total_bytes', 0),
            'latency': simulation.traffic_generator.get_traffic_stats().get('avg_latency_ms', 0),
            'bandwidth': simulation.traffic_generator.get_traffic_stats().get('current_bandwidth_mbps', 0)
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