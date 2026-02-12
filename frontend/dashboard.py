from networkx import nodes
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import requests
import json
from typing import Dict, List, Optional

# ============ API CONFIGURATION ============
# Define your API endpoints (to be implemented later)
API_BASE_URL = "http://localhost:8000/api/v1"  # Change this to your backend URL

# API endpoints structure
API_ENDPOINTS = {
    "network_status": f"{API_BASE_URL}/network/status",
    "nodes": f"{API_BASE_URL}/network/nodes",
    "attacks": f"{API_BASE_URL}/attacks",
    "agents": f"{API_BASE_URL}/agents",
    "honeypots": f"{API_BASE_URL}/honeypots",
    "quarantine": f"{API_BASE_URL}/quarantine",
    "metrics": f"{API_BASE_URL}/metrics",
    "simulation_control": f"{API_BASE_URL}/simulation/control"
}

# ============ MOCK DATA FOR TESTING ============
# This simulates your backend responses until you implement the actual API
class MockBackend:
    """Mock backend to simulate API responses for frontend development"""
    
    @staticmethod
    def get_network_status():
        return {
            "status": "active",
            "total_nodes": 24,
            "active_attacks": 3,
            "quarantined_nodes": 2,
            "honeypots_deployed": 4,
            "threat_level": "Medium",
            "total_traffic": 45.2,
            "last_updated": datetime.now().isoformat()
        }
    
    @staticmethod
    def get_nodes():
        nodes = []
        # Generate mock nodes with various states
        node_types = ["Workstation", "Server", "Firewall", "Switch", "IoT", "Honeypot"]
        statuses = ["Healthy", "Compromised", "Quarantined", "Under Attack", "Monitoring"]
    
        for i in range(1, 21): 
            status = np.random.choice(statuses, p=[0.6, 0.1, 0.1, 0.1, 0.1])
            node_type = np.random.choice(node_types)
        
            connections = []
        
            if i <= 16:  # Workstations connect to servers
                connections.append(np.random.randint(17, 21))  # Connect to servers
            else:  # Servers connect to each other
                connections = [17, 18, 19, 20]
                connections.remove(i)
        
            # Add some random connections
            num_connections = np.random.randint(1, 4)
            for _ in range(num_connections):
                conn = np.random.randint(1, 21)
                if conn != i and conn not in connections:
                    connections.append(conn)
        
            nodes.append({
                "id": f"node-{i:03d}",
                "name": f"{node_type}-{i:02d}",
                "type": node_type,
                "status": status,
                "ip": f"192.168.1.{i}",
                "os": np.random.choice(["Windows", "Linux", "macOS"]),
                "threat_score": np.random.randint(0, 100) if status == "Compromised" else 0,
                "connections": connections,
                "last_seen": (datetime.now() - timedelta(minutes=np.random.randint(1, 60))).isoformat(),
                "is_compromised": status == "Compromised",
                "is_quarantined": status == "Quarantined",
                "is_honeypot": node_type == "Honeypot"
            })
        return nodes
    
    @staticmethod
    def get_active_attacks():
        attacks = [
            {"id": 1, "type": "Port Scan", "source": "192.168.1.105", "target": "Server-01", 
             "severity": "Low", "status": "Active", "started": "10:00", "agent_action": "Monitoring"},
            {"id": 2, "type": "DDoS", "source": "Multiple", "target": "Web Server", 
             "severity": "High", "status": "Active", "started": "10:01", "agent_action": "Rate limiting"},
            {"id": 3, "type": "Malware", "source": "Workstation-12", "target": "Database", 
             "severity": "Medium", "status": "Contained", "started": "10:02", "agent_action": "Quarantined"}
        ]
        return attacks
    
    @staticmethod
    def get_agent_actions():
        actions = [
            {"agent": "Agent-01", "action": "Detected port scan on Server-01", "timestamp": "10:00:23", "severity": "Low"},
            {"agent": "Agent-03", "action": "Deployed honeypot at 192.168.1.100", "timestamp": "10:01:15", "severity": "Info"},
            {"agent": "Agent-02", "action": "Quarantined Workstation-12 due to malware", "timestamp": "10:02:47", "severity": "High"},
            {"agent": "Agent-01", "action": "Analyzing traffic pattern from 192.168.1.105", "timestamp": "10:03:12", "severity": "Medium"},
            {"agent": "Agent-04", "action": "Honeypot triggered by suspicious activity", "timestamp": "10:04:05", "severity": "Critical"}
        ]
        return actions
    
    @staticmethod
    def get_metrics():
        # Generate time series data
        times = [(datetime.now() - timedelta(minutes=i)).strftime("%H:%M") for i in range(20, 0, -1)]
        return {
            "traffic_history": {
                "times": times,
                "values": np.random.randint(20, 100, size=20).tolist()
            },
            "threat_history": {
                "times": times,
                "values": np.random.randint(0, 100, size=20).tolist()
            },
            "node_history": {
                "times": times,
                "healthy": np.random.randint(20, 25, size=20).tolist(),
                "compromised": np.random.randint(0, 5, size=20).tolist(),
                "quarantined": np.random.randint(0, 3, size=20).tolist()
            }
        }

# ============ API CLIENT ============
class APIClient:
    """Client for making API requests to backend"""
    
    def __init__(self, use_mock=True):
        self.use_mock = use_mock
        self.mock = MockBackend()
    
    def get(self, endpoint, params=None):
        """Generic GET request"""
        if self.use_mock:
            # Route to appropriate mock method based on endpoint
            if "network/status" in endpoint:
                return self.mock.get_network_status()
            elif "network/nodes" in endpoint:
                return self.mock.get_nodes()
            elif "attacks" in endpoint:
                return self.mock.get_active_attacks()
            elif "agents" in endpoint:
                return self.mock.get_agent_actions()
            elif "metrics" in endpoint:
                return self.mock.get_metrics()
            else:
                return {}
        else:
            try:
                response = requests.get(endpoint, params=params)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                st.error(f"API Error: {e}")
                return None
    
    def post(self, endpoint, data=None):
        """Generic POST request"""
        if self.use_mock:
            return {"status": "success", "message": f"Mock POST to {endpoint}"}
        else:
            try:
                response = requests.post(endpoint, json=data)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                st.error(f"API Error: {e}")
                return None

# ============ VISUALIZATION FUNCTIONS ============
def create_network_graph(nodes):
    """Create an interactive network graph using Plotly"""
    
    if not nodes:
        fig = go.Figure()
        fig.update_layout(
            title='Network Topology (No Data)',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=600
        )
        return fig
    
    # Create node positions
    np.random.seed(42)
    n_nodes = len(nodes)
    
    # Use a circular layout for better edge visibility
    angles = np.linspace(0, 2*np.pi, n_nodes, endpoint=False)
    radius = 3
    x_positions = radius * np.cos(angles)
    y_positions = radius * np.sin(angles)
    
    # Assign positions to nodes
    for i, node in enumerate(nodes):
        node['x'] = x_positions[i]
        node['y'] = y_positions[i]
    
    # Create edges - FIXED: Better edge creation logic
    edge_x = []
    edge_y = []
    
    # Track unique connections to avoid duplicates
    connections_added = set()
    
    for i, node in enumerate(nodes):
        node_x = node['x']
        node_y = node['y']
        
        # Get connections - ensure it's a list
        connections = node.get('connections', [])
        if isinstance(connections, (int, float)):
            connections = [connections]
        elif not isinstance(connections, list):
            connections = []
        
        for connection in connections:
            # Convert to int if possible
            try:
                conn_idx = int(connection)
            except (ValueError, TypeError):
                continue
                
            # Check if connection is valid
            if 0 <= conn_idx < len(nodes) and conn_idx != i:
                # Create a unique key for this connection (avoid duplicates)
                conn_key = tuple(sorted([i, conn_idx]))
                
                if conn_key not in connections_added:
                    connections_added.add(conn_key)
                    
                    # Add line from node to connection
                    edge_x.extend([node_x, nodes[conn_idx]['x'], None])
                    edge_y.extend([node_y, nodes[conn_idx]['y'], None])
    
    # Create edge trace with more visible styling
    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        mode='lines',
        line=dict(
            color='rgba(100,100,255,0.4)',  # Blue-ish color for better visibility
            width=1.5,
            dash=None
        ),
        hoverinfo='none',
        name='Network Connections'
    )
    
    # Group nodes by status
    healthy_nodes = []
    compromised_nodes = []
    quarantined_nodes = []
    honeypot_nodes = []
    monitoring_nodes = []
    under_attack_nodes = []
    
    for node in nodes:
        if node.get('is_honeypot', False):
            honeypot_nodes.append(node)
        elif node.get('is_compromised', False):
            compromised_nodes.append(node)
        elif node.get('is_quarantined', False):
            quarantined_nodes.append(node)
        elif node.get('status') == 'Under Attack':
            under_attack_nodes.append(node)
        elif node.get('status') == 'Monitoring':
            monitoring_nodes.append(node)
        else:
            healthy_nodes.append(node)
    
    node_traces = []
    
    # Healthy nodes
    if healthy_nodes:
        node_traces.append(go.Scatter(
            x=[n['x'] for n in healthy_nodes],
            y=[n['y'] for n in healthy_nodes],
            mode='markers+text',
            marker=dict(
                size=25,
                color='#2ecc71',
                line=dict(color='#27ae60', width=2),
                symbol='circle'
            ),
            text=[n.get('name', f"Node-{i}") for i, n in enumerate(healthy_nodes)],
            textposition="top center",
            textfont=dict(size=10),
            name='Healthy',
            hoverinfo='text',
            hovertext=[f"✅ HEALTHY<br>Name: {n.get('name', 'Unknown')}<br>IP: {n.get('ip', 'Unknown')}<br>Type: {n.get('type', 'Unknown')}" 
                      for n in healthy_nodes]
        ))
    
    # Compromised nodes
    if compromised_nodes:
        node_traces.append(go.Scatter(
            x=[n['x'] for n in compromised_nodes],
            y=[n['y'] for n in compromised_nodes],
            mode='markers+text',
            marker=dict(
                size=30,
                color='#e74c3c',
                line=dict(color='#c0392b', width=2),
                symbol='x',
                opacity=0.9
            ),
            text=[n.get('name', f"Node-{i}") for i, n in enumerate(compromised_nodes)],
            textposition="top center",
            textfont=dict(size=10, color='red'),
            name='Compromised',
            hoverinfo='text',
            hovertext=[f"⚠️ COMPROMISED ⚠️<br>Name: {n.get('name', 'Unknown')}<br>IP: {n.get('ip', 'Unknown')}<br>Threat Score: {n.get('threat_score', 'N/A')}" 
                      for n in compromised_nodes]
        ))
    
    # Quarantined nodes
    if quarantined_nodes:
        node_traces.append(go.Scatter(
            x=[n['x'] for n in quarantined_nodes],
            y=[n['y'] for n in quarantined_nodes],
            mode='markers+text',
            marker=dict(
                size=28,
                color='#f39c12',
                line=dict(color='#e67e22', width=2),
                symbol='square'
            ),
            text=[n.get('name', f"Node-{i}") for i, n in enumerate(quarantined_nodes)],
            textposition="top center",
            textfont=dict(size=10),
            name='Quarantined',
            hoverinfo='text',
            hovertext=[f"🔒 QUARANTINED<br>Name: {n.get('name', 'Unknown')}<br>IP: {n.get('ip', 'Unknown')}" 
                      for n in quarantined_nodes]
        ))
    
    # Honeypot nodes
    if honeypot_nodes:
        node_traces.append(go.Scatter(
            x=[n['x'] for n in honeypot_nodes],
            y=[n['y'] for n in honeypot_nodes],
            mode='markers+text',
            marker=dict(
                size=28,
                color='#9b59b6',
                line=dict(color='#8e44ad', width=2),
                symbol='diamond'
            ),
            text=[n.get('name', f"Node-{i}") for i, n in enumerate(honeypot_nodes)],
            textposition="top center",
            textfont=dict(size=10),
            name='Honeypot',
            hoverinfo='text',
            hovertext=[f"🍯 HONEYPOT<br>Name: {n.get('name', 'Unknown')}<br>IP: {n.get('ip', 'Unknown')}" 
                      for n in honeypot_nodes]
        ))
    
    # Under Attack nodes
    if under_attack_nodes:
        node_traces.append(go.Scatter(
            x=[n['x'] for n in under_attack_nodes],
            y=[n['y'] for n in under_attack_nodes],
            mode='markers+text',
            marker=dict(
                size=28,
                color='#e67e22',
                line=dict(color='#d35400', width=2),
                symbol='circle'
            ),
            text=[n.get('name', f"Node-{i}") for i, n in enumerate(under_attack_nodes)],
            textposition="top center",
            textfont=dict(size=10),
            name='Under Attack',
            hoverinfo='text',
            hovertext=[f"🔥 UNDER ATTACK<br>Name: {n.get('name', 'Unknown')}<br>IP: {n.get('ip', 'Unknown')}" 
                      for n in under_attack_nodes]
        ))
    
    # Monitoring nodes
    if monitoring_nodes:
        node_traces.append(go.Scatter(
            x=[n['x'] for n in monitoring_nodes],
            y=[n['y'] for n in monitoring_nodes],
            mode='markers+text',
            marker=dict(
                size=25,
                color='#3498db',
                line=dict(color='#2980b9', width=2),
                symbol='circle'
            ),
            text=[n.get('name', f"Node-{i}") for i, n in enumerate(monitoring_nodes)],
            textposition="top center",
            textfont=dict(size=10),
            name='Monitoring',
            hoverinfo='text',
            hovertext=[f"🔍 MONITORING<br>Name: {n.get('name', 'Unknown')}<br>IP: {n.get('ip', 'Unknown')}" 
                      for n in monitoring_nodes]
        ))
    
    # Combine all traces - edges FIRST so they appear behind nodes
    all_traces = [edge_trace] + node_traces
    
    # Calculate layout bounds
    all_x = [node['x'] for node in nodes]
    all_y = [node['y'] for node in nodes]
    x_range = [min(all_x) - 1, max(all_x) + 1]
    y_range = [min(all_y) - 1, max(all_y) + 1]
    
    # Create figure
    fig = go.Figure(
        data=all_traces,
        layout=go.Layout(
            title=dict(
                text='Network Topology with Connections',
                font=dict(size=16)
            ),
            showlegend=True,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                range=x_range
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                range=y_range
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=600,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(255,255,255,0.8)'
            )
        )
    )
    
    return fig

def create_threat_gauge(threat_level, value):
    """Create a gauge chart for threat level"""
    colors = ['#2ecc71', '#f39c12', '#e74c3c']
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"Threat Level: {threat_level}"},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1},
            'bar': {'color': colors[1 if threat_level == "Medium" else 2 if threat_level == "High" else 0]},
            'steps': [
                {'range': [0, 33], 'color': '#d5f5e3'},
                {'range': [33, 66], 'color': '#fcf3cf'},
                {'range': [66, 100], 'color': '#fadbd8'}
            ],
            'threshold': {
                'line': {'color': 'red', 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))
    
    fig.update_layout(height=200, margin=dict(l=20, r=20, t=50, b=20))
    return fig

# ============ MAIN DASHBOARD ============
def main():
    st.set_page_config(
        page_title="Aegis Guard - AI Network Security",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            color: #1e3a8a;
            text-align: center;
            margin-bottom: 1rem;
        }
        .metric-card {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .agent-action {
            background-color: #e8f4f8;
            padding: 0.5rem;
            border-radius: 5px;
            margin-bottom: 0.5rem;
            border-left: 4px solid #3498db;
        }
        .critical-action {
            border-left: 4px solid #e74c3c;
        }
        .stButton>button {
            width: 100%;
            background-color: #1e3a8a;
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize API client
    if 'api_client' not in st.session_state:
        st.session_state.api_client = APIClient(use_mock=True)  # Set to False when backend is ready
    
    # Initialize session state for simulation control
    if 'simulation_running' not in st.session_state:
        st.session_state.simulation_running = False
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = True
    
    # Header
    st.markdown('<h1 class="main-header">🛡️ Aegis Guard - AI Orchestrated Network Security</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50?text=Aegis+Guard", width=200)  # Replace with your logo
        
        st.header("🚀 Simulation Control")
        
        # Simulation controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Start" if not st.session_state.simulation_running else "⏸️ Pause"):
                st.session_state.simulation_running = not st.session_state.simulation_running
                st.rerun()
        
        with col2:
            if st.button("🔄 Reset"):
                st.success("Simulation reset!")
        
        st.divider()
        
        # Attack injection
        st.subheader("🎯 Inject Attack")
        attack_type = st.selectbox(
            "Select attack type",
            ["Port Scan", "DDoS", "Malware", "Brute Force", "Man-in-the-Middle", "Ransomware"]
        )
        
        target = st.selectbox("Target node", [f"Node-{i:02d}" for i in range(1, 11)])
        
        if st.button("⚡ Inject Attack"):
            st.warning(f"Injecting {attack_type} attack on {target}")
            # API call would go here
        
        st.divider()
        
        # Honeypot deployment
        st.subheader("🍯 Honeypot Deployment")
        honeypot_type = st.selectbox("Honeypot type", ["Low Interaction", "Medium Interaction", "High Interaction"])
        
        if st.button("Deploy Honeypot"):
            st.success(f"Deploying {honeypot_type} honeypot")
            # API call would go here
        
        st.divider()
        
        # Dashboard settings
        st.subheader("⚙️ Settings")
        st.session_state.auto_refresh = st.checkbox("Auto-refresh", value=st.session_state.auto_refresh)
        refresh_rate = st.slider("Refresh rate (seconds)", 1, 30, 5)
        
        if st.button("🔄 Refresh Now"):
            st.rerun()
        
        # API Connection status
        st.divider()
        st.subheader("🔌 Backend Status")
        if st.session_state.api_client.use_mock:
            st.info("📱 Using mock data (backend not connected)")
            if st.button("Try connect to backend"):
                st.session_state.api_client.use_mock = False
                st.rerun()
        else:
            st.success("✅ Connected to backend")
            if st.button("Switch to mock"):
                st.session_state.api_client.use_mock = True
                st.rerun()
    
    # Main dashboard area
    # Fetch data from API
    network_status = st.session_state.api_client.get(API_ENDPOINTS["network_status"])
    nodes = st.session_state.api_client.get(API_ENDPOINTS["nodes"])
    attacks = st.session_state.api_client.get(API_ENDPOINTS["attacks"])
    agent_actions = st.session_state.api_client.get(API_ENDPOINTS["agents"])
    metrics = st.session_state.api_client.get(API_ENDPOINTS["metrics"])
    
    # Top metrics row
    st.header("📊 Network Overview")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Nodes",
            network_status.get('total_nodes', 0),
            delta=None,
            help="Total number of devices in the network"
        )
    
    with col2:
        st.metric(
            "Active Attacks",
            network_status.get('active_attacks', 0),
            delta="+2" if network_status.get('active_attacks', 0) > 0 else "0",
            delta_color="inverse",
            help="Currently active security threats"
        )
    
    with col3:
        st.metric(
            "Quarantined",
            network_status.get('quarantined_nodes', 0),
            help="Nodes isolated from the network"
        )
    
    with col4:
        st.metric(
            "Honeypots",
            network_status.get('honeypots_deployed', 0),
            help="Active honeypots catching attackers"
        )
    
    with col5:
        threat_value = 45 if network_status.get('threat_level') == "Medium" else 75 if network_status.get('threat_level') == "High" else 20
        st.metric(
            "Threat Level",
            network_status.get('threat_level', "Medium"),
            help="Overall threat severity"
        )
    
    st.divider()
    
    # Main content area
    col_network, col_stats = st.columns([2, 1])
    
    with col_network:
        st.header("🌐 Network Visualization")
        
        if nodes:
            fig = create_network_graph(nodes)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No network data available")
        
        # Legend
        col_legend1, col_legend2, col_legend3, col_legend4, col_legend5 = st.columns(5)
        with col_legend1:
            st.markdown("🟢 **Healthy**")
        with col_legend2:
            st.markdown("🔴 **Compromised**")
        with col_legend3:
            st.markdown("🟠 **Quarantined**")
        with col_legend4:
            st.markdown("🟣 **Honeypot**")
        with col_legend5:
            st.markdown("🔵 **Monitoring**")
    
    with col_stats:
        st.header("📈 Live Metrics")
        
        # Threat gauge
        threat_gauge = create_threat_gauge(
            network_status.get('threat_level', "Medium"),
            threat_value
        )
        st.plotly_chart(threat_gauge, use_container_width=True)
        
        # Traffic graph
        if metrics and 'traffic_history' in metrics:
            traffic_df = pd.DataFrame({
                'Time': metrics['traffic_history']['times'],
                'Traffic (Mbps)': metrics['traffic_history']['values']
            })
            
            fig_traffic = px.line(
                traffic_df, 
                x='Time', 
                y='Traffic (Mbps)',
                title='Network Traffic',
                color_discrete_sequence=['#3498db']
            )
            fig_traffic.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_traffic, use_container_width=True)
        
        # Node status distribution
        if metrics and 'node_history' in metrics:
            node_df = pd.DataFrame({
                'Time': metrics['node_history']['times'][-10:],
                'Healthy': metrics['node_history']['healthy'][-10:],
                'Compromised': metrics['node_history']['compromised'][-10:],
                'Quarantined': metrics['node_history']['quarantined'][-10:]
            })
            
            fig_nodes = px.area(
                node_df,
                x='Time',
                y=['Healthy', 'Compromised', 'Quarantined'],
                title='Node Status Over Time',
                color_discrete_map={
                    'Healthy': '#2ecc71',
                    'Compromised': '#e74c3c',
                    'Quarantined': '#f39c12'
                }
            )
            fig_nodes.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_nodes, use_container_width=True)
    
    # Second row
    st.divider()
    col_attacks, col_agents = st.columns(2)
    
    with col_attacks:
        st.header("⚠️ Active Attacks & Threats")
        
        if attacks:
            attack_df = pd.DataFrame(attacks)
            
            # Color code severity
            def color_severity(val):
                colors = {'Low': 'green', 'Medium': 'orange', 'High': 'red', 'Critical': 'darkred'}
                return f'color: {colors.get(val, "black")}; font-weight: bold'
            
            st.dataframe(
                attack_df,
                column_config={
                    "type": "Attack Type",
                    "source": "Source",
                    "target": "Target",
                    "severity": st.column_config.TextColumn("Severity", help="Threat severity level"),
                    "status": "Status",
                    "agent_action": "Agent Action"
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("✅ No active attacks detected")
        
        # Attack timeline
        st.subheader("Attack Timeline")
        timeline_data = pd.DataFrame({
            "Time": ["10:00", "10:01", "10:02", "10:03", "10:04"],
            "Event": ["Port Scan Detected", "DDoS Attack Started", "Malware Quarantined", "Honeypot Triggered", "Threat Contained"],
            "Severity": ["Low", "High", "Medium", "Critical", "Low"]
        })
        st.dataframe(timeline_data, use_container_width=True, hide_index=True)
    
    with col_agents:
        st.header("🤖 AI Agent Actions")
        
        if agent_actions:
            for action in agent_actions[:5]:
                severity_class = "critical-action" if action.get('severity') == "Critical" else ""
                st.markdown(f"""
                    <div class="agent-action {severity_class}">
                        <strong>🕐 {action.get('timestamp')}</strong> - {action.get('agent')}<br>
                        {action.get('action')}<br>
                        <small>Severity: {action.get('severity')}</small>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No recent agent actions")
        
        # Compromised nodes
        st.subheader("⚠️ Compromised Nodes")
        if nodes:
            compromised = [n for n in nodes if n.get('is_compromised', False)]
            if compromised:
                for node in compromised[:5]:
                    st.error(f"🔴 **{node.get('name')}** - {node.get('ip')}")
                    st.caption(f"Threat Score: {node.get('threat_score')}")
            else:
                st.success("✅ No compromised nodes")
        
        # Quarantined nodes
        st.subheader("🔒 Quarantined Nodes")
        if nodes:
            quarantined = [n for n in nodes if n.get('is_quarantined', False)]
            if quarantined:
                for node in quarantined[:3]:
                    st.warning(f"🟠 **{node.get('name')}** - Isolated")
            else:
                st.info("No quarantined nodes")
    
    # Third row - Additional controls and analysis
    st.divider()
    st.header("🛠️ Security Operations")
    
    col_honeypot, col_response, col_analysis = st.columns(3)
    
    with col_honeypot:
        st.subheader("🍯 Honeypot Strategy")
        st.info("**Current Strategy:** Deceptive Layer")
        st.write("• 4 active honeypots")
        st.write("• 12 attacks diverted")
        st.write("• 3 attackers identified")
        
        if st.button("Deploy New Honeypot"):
            st.success("Honeypot deployed at 192.168.1.100")
    
    with col_response:
        st.subheader("⚡ Automated Response")
        response_policies = {
            "Port Scan": "Rate Limiting",
            "DDoS": "Traffic Filtering",
            "Malware": "Immediate Quarantine",
            "Brute Force": "IP Blocking"
        }
        
        for attack, response in response_policies.items():
            st.checkbox(f"{attack} → {response}", value=True)
    
    with col_analysis:
        st.subheader("📊 Threat Intelligence")
        
        # Pie chart for attack types
        attack_types = ['Port Scan', 'DDoS', 'Malware', 'Brute Force']
        attack_counts = [15, 7, 5, 3]
        
        fig_pie = px.pie(
            values=attack_counts,
            names=attack_types,
            title="Attack Distribution",
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        fig_pie.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Footer
    st.divider()
    st.caption("🛡️ Aegis Guard - AI Orchestrated Network Security System | Olympiad Project")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Auto-refresh: {'ON' if st.session_state.auto_refresh else 'OFF'}")
    
    # Auto-refresh logic
    if st.session_state.auto_refresh and st.session_state.simulation_running:
        time.sleep(refresh_rate)
        st.rerun()

# ============ API DEFINITION DOCUMENTATION ============
def api_documentation():
    """This function documents the API endpoints that need to be implemented in the backend"""
    
    docs = """
    # Aegis Guard API Specification v1.0
    
    ## Base URL
    `http://localhost:8000/api/v1`
    
    ## Endpoints
    
    ### GET /network/status
    Get overall network status
    **Response:**
    ```json
    {
        "status": "active",
        "total_nodes": 24,
        "active_attacks": 3,
        "quarantined_nodes": 2,
        "honeypots_deployed": 4,
        "threat_level": "Medium",
        "total_traffic": 45.2,
        "last_updated": "2024-01-01T10:00:00"
    }
    ```
    
    ### GET /network/nodes
    Get all network nodes
    **Response:**
    ```json
    [
        {
            "id": "node-001",
            "name": "Server-01",
            "type": "Server",
            "status": "Healthy",
            "ip": "192.168.1.1",
            "os": "Linux",
            "threat_score": 0,
            "connections": [2, 3, 5],
            "last_seen": "2024-01-01T10:00:00",
            "is_compromised": false,
            "is_quarantined": false,
            "is_honeypot": false
        }
    ]
    ```
    
    ### GET /attacks
    Get active attacks
    ### POST /attacks/inject
    Inject new attack
    ### GET /agents
    Get agent actions
    ### POST /honeypots/deploy
    Deploy new honeypot
    ### POST /quarantine/{node_id}
    Quarantine a node
    ### GET /metrics
    Get historical metrics
    ### POST /simulation/control
    Control simulation state
    """
    
    return docs

if __name__ == "__main__":
    main()