import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import requests
import json
from datetime import datetime, timedelta
import time
import socketio

# ============ CONFIGURATION ============
st.set_page_config(
    page_title="Aegis Guard - AI Network Security",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
SOCKET_URL = "http://localhost:8000"

# ============ API CLIENT ============
class APIClient:
    """Real API client for backend communication"""
    
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        
    def get(self, endpoint, params=None):
        """Make GET request to API"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, params=params, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            st.error(f"❌ Cannot connect to backend at {self.base_url}. Make sure the Flask server is running.")
            return None
        except requests.exceptions.Timeout:
            st.error("❌ Request timeout - backend is not responding")
            return None
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                st.warning(f"⚠️ Endpoint not found: {endpoint}")
            else:
                st.error(f"❌ HTTP Error {response.status_code}: {e}")
            return None
        except Exception as e:
            st.error(f"❌ API Error: {str(e)}")
            return None
    
    def post(self, endpoint, data=None):
        """Make POST request to API"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.post(url, json=data, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            st.error(f"❌ Cannot connect to backend at {self.base_url}")
            return None
        except requests.exceptions.Timeout:
            st.error("❌ Request timeout")
            return None
        except Exception as e:
            st.error(f"❌ API Error: {str(e)}")
            return None
    
    def put(self, endpoint, data=None):
        """Make PUT request to API"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.put(url, json=data, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"❌ API Error: {str(e)}")
            return None
    
    def delete(self, endpoint):
        """Make DELETE request to API"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.delete(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"❌ API Error: {str(e)}")
            return None

# ============ WEBSOCKET CLIENT ============
class SocketIOClient:
    def __init__(self):
        self.sio = socketio.Client()
        self.connected = False
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.sio.event
        def connect():
            self.connected = True
            st.sidebar.success("✅ WebSocket Connected")
        
        @self.sio.event
        def disconnect():
            self.connected = False
            st.sidebar.warning("⚠️ WebSocket Disconnected")
        
        @self.sio.on('simulation_update')
        def on_simulation_update(data):
            st.session_state.simulation_state = data
            if 'last_update' in st.session_state:
                st.session_state.last_update = datetime.now()
        
        @self.sio.on('simulation_state_change')
        def on_state_change(data):
            st.session_state.simulation_running = (data.get('state') == 'running')
            st.success(f"🔄 Simulation state changed to: {data.get('state')}")
    
    def connect(self):
        try:
            self.sio.connect(SOCKET_URL)
        except:
            st.sidebar.warning("⚠️ Could not connect to WebSocket")
    
    def disconnect(self):
        if self.connected:
            self.sio.disconnect()
    
    def request_update(self, timedelta_seconds=5):
        if self.connected:
            self.sio.emit('request_update', {'timedelta': timedelta_seconds})

# ============ VISUALIZATION FUNCTIONS ============
def create_network_graph(nodes):
    """Create an interactive network graph using Plotly"""
    
    if not nodes:
        fig = go.Figure()
        fig.update_layout(
            title='Network Topology (No Data)',
            height=600
        )
        return fig
    
    # Create node positions using force-directed layout
    np.random.seed(42)
    n_nodes = len(nodes)
    
    # Use circular layout
    angles = np.linspace(0, 2*np.pi, n_nodes, endpoint=False)
    radius = 3
    x_positions = radius * np.cos(angles)
    y_positions = radius * np.sin(angles)
    
    # Assign positions
    for i, node in enumerate(nodes):
        node['x'] = x_positions[i]
        node['y'] = y_positions[i]
    
    # Create edges
    edge_x = []
    edge_y = []
    connections_added = set()
    
    for i, node in enumerate(nodes):
        for conn in node.get('connections', []):
            if isinstance(conn, (int, str)):
                try:
                    conn_idx = int(conn) - 1 if isinstance(conn, str) and conn.startswith('node-') else int(conn)
                    if 0 <= conn_idx < n_nodes and conn_idx != i:
                        conn_key = tuple(sorted([i, conn_idx]))
                        if conn_key not in connections_added:
                            connections_added.add(conn_key)
                            edge_x.extend([node['x'], nodes[conn_idx]['x'], None])
                            edge_y.extend([node['y'], nodes[conn_idx]['y'], None])
                except (ValueError, IndexError):
                    continue
    
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        mode='lines',
        line=dict(color='rgba(100,100,255,0.3)', width=1.5),
        hoverinfo='none',
        name='Connections'
    )
    
    # Group nodes by status
    status_groups = {
        'Healthy': {'color': '#2ecc71', 'symbol': 'circle', 'size': 25},
        'Compromised': {'color': '#e74c3c', 'symbol': 'x', 'size': 30},
        'Quarantined': {'color': '#f39c12', 'symbol': 'square', 'size': 28},
        'Honeypot': {'color': '#9b59b6', 'symbol': 'diamond', 'size': 28},
        'Monitoring': {'color': '#3498db', 'symbol': 'circle', 'size': 25},
        'Under Attack': {'color': '#e67e22', 'symbol': 'circle', 'size': 28}
    }
    
    node_traces = []
    
    for status, style in status_groups.items():
        group_nodes = [n for n in nodes if n.get('status') == status or 
                      (status == 'Honeypot' and n.get('is_honeypot')) or
                      (status == 'Compromised' and n.get('is_compromised')) or
                      (status == 'Quarantined' and n.get('is_quarantined'))]
        
        if group_nodes:
            trace = go.Scatter(
                x=[n['x'] for n in group_nodes],
                y=[n['y'] for n in group_nodes],
                mode='markers+text',
                marker=dict(
                    size=style['size'],
                    color=style['color'],
                    line=dict(color='white', width=2),
                    symbol=style['symbol'],
                    opacity=0.9 if status == 'Compromised' else 1
                ),
                text=[n.get('name', '') for n in group_nodes],
                textposition="top center",
                textfont=dict(size=9, color='black'),
                name=status,
                hoverinfo='text',
                hovertext=[
                    f"<b>{status.upper()}</b><br>" +
                    f"Name: {n.get('name', 'Unknown')}<br>" +
                    f"IP: {n.get('ip', 'Unknown')}<br>" +
                    f"Type: {n.get('type', 'Unknown')}<br>" +
                    f"OS: {n.get('os', 'Unknown')}"
                    for n in group_nodes
                ]
            )
            node_traces.append(trace)
    
    # Create figure
    fig = go.Figure(
        data=[edge_trace] + node_traces,
        layout=go.Layout(
            title=dict(
                text='Network Topology',
                font=dict(size=16)
            ),
            showlegend=True,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
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
    colors = {'Low': '#2ecc71', 'Medium': '#f39c12', 'High': '#e74c3c'}
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"Threat Level: {threat_level}"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': colors.get(threat_level, '#f39c12')},
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
    # Custom CSS
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
        }
        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        .status-running {
            background-color: #d5f5e3;
            color: #27ae60;
        }
        .status-stopped {
            background-color: #fadbd8;
            color: #e74c3c;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'api_client' not in st.session_state:
        st.session_state.api_client = APIClient(API_BASE_URL)
    
    if 'socket_client' not in st.session_state:
        st.session_state.socket_client = SocketIOClient()
    
    if 'simulation_running' not in st.session_state:
        st.session_state.simulation_running = False
    
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = True
    
    if 'last_update' not in st.session_state:
        st.session_state.last_update = datetime.now()
    
    # Header
    st.markdown('<h1 class="main-header">🛡️ Aegis Guard - AI Orchestrated Network Security</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50?text=Aegis+Guard", width=200)
        
        # Connection status
        st.subheader("🔌 Connection Status")
        col1, col2 = st.columns(2)
        with col1:
            if st.session_state.socket_client.connected:
                st.markdown("✅ **WebSocket**")
            else:
                st.markdown("❌ **WebSocket**")
        with col2:
            st.markdown("✅ **API**")
        
        if st.button("🔄 Connect WebSocket"):
            st.session_state.socket_client.connect()
        
        st.divider()
        
        # Simulation control
        st.header("🚀 Simulation Control")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Start" if not st.session_state.simulation_running else "⏸️ Pause"):
                action = "start" if not st.session_state.simulation_running else "pause"
                result = st.session_state.api_client.post('/simulation/control', {'action': action})
                if result:
                    st.session_state.simulation_running = (action == "start")
                    st.rerun()
        
        with col2:
            if st.button("🔄 Reset"):
                result = st.session_state.api_client.post('/simulation/control', {'action': 'reset'})
                if result:
                    st.session_state.simulation_running = False
                    st.success("Simulation reset!")
                    st.rerun()
        
        # Simulation state
        state_response = st.session_state.api_client.get('/simulation/state')
        if state_response:
            sim_state = state_response.get('state', 'stopped')
            state_class = "status-running" if sim_state == "running" else "status-stopped"
            st.markdown(f"**State:** <span class='status-badge {state_class}'>{sim_state.upper()}</span>", unsafe_allow_html=True)
        
        st.divider()
        
        # Attack injection
        st.subheader("🎯 Inject Attack")
        attacks = ["Port Scan", "DDoS", "Malware", "ARP Spoofing", "SQL Injection", "Brute Force", "XSS", "CSRF", "Zero-Day"]
        attack_type = st.selectbox(
            "Attack type",
            attacks
        )
        index = attacks.index(attack_type)
        attack_types = ['port_scan', 'ddos', 'malware_spread', 'arp_spoofing', 'sql_injection', 'brute_force', 'xss', 'csrf', 'zero_day']
        attack_type = attack_types[index]
        
        # Get nodes for target selection
        nodes = st.session_state.api_client.get('/network/nodes') or []
        node_names = [n.get('name', f"Node-{i}") for i, n in enumerate(nodes[:10])]
        target = st.selectbox("Target node", node_names if node_names else ["Server-01"])
        
        severity = st.select_slider("Severity", ["Low", "Medium", "High", "Critical"])
        
        if st.button("⚡ Inject Attack"):
            result = st.session_state.api_client.post('/attacks/inject', {
                'type': attack_type,
                'target': target,
                'severity': severity
            })
            if result:
                st.success(f"✅ {attack_type} attack injected on {target}")
                st.balloons()
        
        st.divider()
        
        # Honeypot deployment
        st.subheader("🍯 Honeypot Deployment")
        honeypot_name = st.text_input("Honeypot name", "Honeypot-01")
        honeypot_type = st.selectbox("Type", ["Low Interaction", "Medium Interaction", "High Interaction"])
        
        if st.button("Deploy Honeypot"):
            result = st.session_state.api_client.post('/honeypots/deploy', {
                'name': honeypot_name,
                'type': honeypot_type
            })
            if result:
                st.success(f"✅ {honeypot_name} deployed successfully!")
        
        st.divider()
        
        # Settings
        st.subheader("⚙️ Settings")
        st.session_state.auto_refresh = st.checkbox("Auto-refresh", value=st.session_state.auto_refresh)
        refresh_rate = st.slider("Refresh rate (seconds)", 2, 30, 5)
        
        if st.button("🔄 Refresh Now"):
            st.rerun()
    
    # Main content area
    # Fetch data from API
    with st.spinner("Loading network data..."):
        network_status = st.session_state.api_client.get('/network/status') or {
            'total_nodes': 0, 'active_attacks': 0, 'quarantined_nodes': 0,
            'honeypots_deployed': 0, 'threat_level': 'Unknown', 'total_traffic': 0
        }
        
        nodes = st.session_state.api_client.get('/network/nodes') or []
        attacks = st.session_state.api_client.get('/attacks') or []
        agent_actions = st.session_state.api_client.get('/agents/actions') or []
        honeypots = st.session_state.api_client.get('/honeypots') or []
        metrics = st.session_state.api_client.get('/metrics') or {}
        
        # Request WebSocket update if connected
        if st.session_state.socket_client.connected:
            st.session_state.socket_client.request_update(timedelta_seconds=refresh_rate)
    
    # Top metrics row
    st.header("📊 Network Overview")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Nodes",
            network_status.get('total_nodes', 0),
            help="Total devices in network"
        )
    
    with col2:
        delta = network_status.get('active_attacks', 0)
        st.metric(
            "Active Attacks",
            delta,
            delta=f"+{delta}" if delta > 0 else "0",
            delta_color="inverse",
            help="Currently active threats"
        )
    
    with col3:
        st.metric(
            "Quarantined",
            network_status.get('quarantined_nodes', 0),
            help="Isolated nodes"
        )
    
    with col4:
        st.metric(
            "Honeypots",
            network_status.get('honeypots_deployed', 0),
            help="Active honeypots"
        )
    
    with col5:
        threat_value = network_status.get('threat_level', 30)
        threat_level = int(threat_value * 100) if isinstance(threat_value, (int, float)) else 30
        st.metric(
            "Threat Level",
            threat_level,
            delta=None,
            help="Overall threat severity"
        )
    
    st.divider()
    
    # Main content row
    col_network, col_stats = st.columns([2, 1])
    
    with col_network:
        st.header("🌐 Network Visualization")
        
        if nodes:
            fig = create_network_graph(nodes)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No network data available. Make sure the backend is running.")
        
        # Legend
        cols = st.columns(5)
        legend_items = [
            ("🟢 Healthy", "#2ecc71"),
            ("🔴 Compromised", "#e74c3c"),
            ("🟠 Quarantined", "#f39c12"),
            ("🟣 Honeypot", "#9b59b6"),
            ("🔵 Monitoring", "#3498db"),
        ]
        for i, (text, color) in enumerate(legend_items):
            with cols[i % 5]:
                st.markdown(f"<span style='color:{color}'>●</span> **{text}**", unsafe_allow_html=True)
    
    with col_stats:
        st.header("📈 Live Metrics")
        threat_enum = "High" if threat_level > 66 else "Medium" if threat_level > 33 else "Low"
        
        # Threat gauge
        threat_gauge = create_threat_gauge(
            threat_enum,
            threat_level
        )
        st.plotly_chart(threat_gauge, use_container_width=True)
        
        # Traffic graph  
        metrics_history = st.session_state.api_client.get('/metrics/history?timeframe=3m') or []
        traffic_df = pd.DataFrame({
            'Time': [m.get('timestamp', '') for m in metrics_history],
            'Traffic (Mbps)': [m.get('traffic_metrics', {}).get('current_bandwidth_mbps', 0) for m in metrics_history]
        })
            
        if not traffic_df.empty:
            fig_traffic = px.line(
                traffic_df, x='Time', y='Traffic (Mbps)',
                title='Network Traffic',
                color_discrete_sequence=['#3498db']
            )
            fig_traffic.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_traffic, use_container_width=True)
        
        # Node distribution
        if nodes:
            status_counts = {}
            for node in nodes:
                status = node.get('status', 'Unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            status_df = pd.DataFrame({
                'Status': list(status_counts.keys()),
                'Count': list(status_counts.values())
            })
            
            fig_pie = px.pie(
                status_df, values='Count', names='Status',
                title='Node Distribution',
                color_discrete_map={
                    'Healthy': '#2ecc71',
                    'Compromised': '#e74c3c',
                    'Quarantined': '#f39c12',
                    'Monitoring': '#3498db',
                    'Under Attack': '#e67e22'
                }
            )
            fig_pie.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_pie, use_container_width=True)
    
    st.divider()
    
    # Second row
    col_attacks, col_agents = st.columns(2)
    
    with col_attacks:
        st.header("⚠️ Active Attacks")
        
        if attacks:
            # Convert attacks to DataFrame
            attack_df = pd.DataFrame(attacks)

            # Color code severity based on float values
            def color_severity(val):
                """
                Color severity based on float value between 0 and 1
                0.0 - 0.3: Low (green)
                0.3 - 0.6: Medium (orange)
                0.6 - 0.9: High (red)
                0.9 - 1.0: Critical (darkred)
                """
                try:
                    # Convert to float if it's a string representation of a number
                    if isinstance(val, str):
                        val = float(val)
                except ValueError:
                    return 'color: black; font-weight: bold'
        
                    # Handle float values
                    if isinstance(val, (int, float)):
                        if val < 0.3:
                            return 'color: #2ecc71; font-weight: bold'  # Green
                        elif val < 0.6:
                            return 'color: #f39c12; font-weight: bold'  # Orange
                        elif val < 0.9:
                            return 'color: #e74c3c; font-weight: bold'  # Red
                        else:
                            return 'color: #8b0000; font-weight: bold'  # Dark Red
                    else:
                        return 'color: black; font-weight: bold'
                except:
                    return 'color: black; font-weight: bold'

            # Apply styling
            styled_df = attack_df.style.map(color_severity, subset=['intensity'])

            # Display the dataframe
            st.dataframe(
                styled_df,
                column_config={
                    "type": "Attack Type",
                    "source": "Source",
                    "target": "Target",
                    "severity": st.column_config.NumberColumn(
                        "Severity",
                        help="Threat severity (0-1)",
                        format="%.2f",  # Show as decimal with 2 places
                        min_value=0,
                        max_value=1
                    ),
                    "status": "Status",
                    "agent_action": "Action"
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("✅ No active attacks detected")
        
        # Attack timeline
        st.subheader("📅 Attack Timeline")
        if attacks:
            timeline_data = []
            for attack in attacks[:5]:
                timeline_data.append({
                    "Time": attack.get('started', 'N/A'),
                    "Event": f"{attack.get('type')} on {attack.get('target')}",
                    "Severity": attack.get('intensity', 'N/A')
                })
            
            if timeline_data:
                timeline_df = pd.DataFrame(timeline_data)
                st.dataframe(timeline_df, use_container_width=True, hide_index=True)
    
    with col_agents:
        st.header("🤖 AI Agent Actions")
        
        if agent_actions:
            for action in agent_actions[:8]:
                severity = action.get('severity', 'Info')
                severity_class = "critical-action" if severity in ["High", "Critical"] else ""
                
                st.markdown(f"""
                    <div class="agent-action {severity_class}">
                        <strong>🕐 {action.get('timestamp', 'N/A')}</strong> - {action.get('agent', 'Agent')}<br>
                        {action.get('action', 'No action')}<br>
                        <small>Severity: {severity}</small>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No recent agent actions")
        
        st.divider()
        
        # Compromised nodes
        st.subheader("⚠️ Compromised Nodes")
        compromised = [n for n in nodes if n.get('is_compromised', False)]
        if compromised:
            for node in compromised[:5]:
                st.error(f"🔴 **{node.get('name')}** - {node.get('ip')}")
                st.caption(f"Threat Score: {node.get('threat_score', 'N/A')}")
        else:
            st.success("✅ No compromised nodes")
        
        # Quarantined nodes
        st.subheader("🔒 Quarantined Nodes")
        quarantined = [n for n in nodes if n.get('is_quarantined', False)]
        if quarantined:
            for node in quarantined[:3]:
                st.warning(f"🟠 **{node.get('name')}**")
                if st.button(f"Release {node.get('name')}", key=f"release_{node.get('id')}"):
                    result = st.session_state.api_client.delete(f"/quarantine/{node.get('id')}")
                    if result:
                        st.success(f"Released {node.get('name')}")
                        st.rerun()
        else:
            st.info("No quarantined nodes")
    
    st.divider()
    
    # Third row - Honeypots
    st.header("🍯 Honeypot Deployment")
    
    col_honeypot_list, col_honeypot_stats = st.columns(2)
    
    with col_honeypot_list:
        st.subheader("Active Honeypots")
        if honeypots:
            for hp in honeypots:
                with st.expander(f"🍯 {hp.get('name')} ({hp.get('type')})"):
                    st.write(f"**IP:** {hp.get('ip', 'N/A')}")
                    st.write(f"**Status:** {hp.get('status', 'Active')}")
                    st.write(f"**Triggers:** {hp.get('triggers', 0)}")
                    
                    if hp.get('attacks_caught'):
                        st.write("**Attacks caught:**")
                        for attack in hp.get('attacks_caught', [])[-3:]:
                            st.caption(f"- {attack.get('attack_type')} at {attack.get('timestamp', 'N/A')}")
                    
                    if st.button(f"Remove {hp.get('name')}", key=f"remove_{hp.get('id')}"):
                        result = st.session_state.api_client.delete(f"/honeypots/{hp.get('id')}")
                        if result:
                            st.success(f"Removed {hp.get('name')}")
                            st.rerun()
        else:
            st.info("No honeypots deployed")
    
    with col_honeypot_stats:
        st.subheader("Honeypot Strategy")
        
        strategy = st.session_state.api_client.get('/honeypots/strategy') or {
            'strategy': 'Deceptive Layer',
            'deployment': 'Strategic placement',
            'types': ['Low Interaction', 'Medium Interaction', 'High Interaction'],
            'current_focus': 'Catching reconnaissance'
        }
        
        st.info(f"**Current Strategy:** {strategy.get('strategy', 'N/A')}")
        st.write(f"**Deployment:** {strategy.get('deployment', 'N/A')}")
        st.write("**Active Types:**")
        for t in strategy.get('types', []):
            st.write(f"- {t}")
        st.write(f"**Focus:** {strategy.get('current_focus', 'N/A')}")
        
        # Honeypot stats
        total_triggers = sum(hp.get('triggers', 0) for hp in honeypots)
        total_attacks = sum(len(hp.get('attacks_caught', [])) for hp in honeypots)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Triggers", total_triggers)
        with col2:
            st.metric("Attacks Caught", total_attacks)
    
    st.divider()
    
    # Footer
    st.caption("🛡️ Aegis Guard - AI Orchestrated Network Security System | Olympiad Project")
    st.caption(f"Last updated: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Auto-refresh logic
    if st.session_state.auto_refresh and st.session_state.simulation_running:
        time.sleep(refresh_rate)
        st.rerun()

# ============ RUN THE APP ============
if __name__ == "__main__":
    main()