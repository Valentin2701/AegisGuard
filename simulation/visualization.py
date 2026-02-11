# Remove the dot from the import
import sys
import os

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation import NetworkGraph

import streamlit as st
import plotly.graph_objects as go
import networkx as nx
import pandas as pd

def create_network_figure(network):
    """Create a Plotly figure from a NetworkGraph object."""
    G = nx.Graph()
    for node_id, node in network.nodes.items():
        G.add_node(node_id, name=node.name, compromised=node.is_compromised)
    for edge in network.edges:
        G.add_edge(edge[0], edge[1])
    
    pos = nx.spring_layout(G, k=0.5, iterations=50)
    
    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    edge_trace = go.Scatter(x=edge_x, y=edge_y, mode='lines',
                            line=dict(width=0.5, color='#888'),
                            hoverinfo='none', showlegend=False)
    
    node_x, node_y, node_color, node_text = [], [], [], []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_color.append('red' if G.nodes[node].get('compromised') else 'blue')
        node_text.append(G.nodes[node].get('name', f"Node {node}"))
    
    node_trace = go.Scatter(x=node_x, y=node_y, mode='markers+text', text=node_text,
                            marker=dict(size=10, color=node_color),
                            hoverinfo='text', showlegend=False)
    
    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(showlegend=False, hovermode='closest',
                      xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                      yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
    return fig

st.set_page_config(layout="wide")
st.title("Aegis Guard Dashboard")

# Sidebar controls
with st.sidebar:
    st.header("Controls")
    network_size = st.selectbox("Network Size", ["Small", "Medium", "Large"])
    simulate = st.button("Start Simulation")
    attack_type = st.selectbox("Inject Attack", ["None", "Port Scan", "DDoS", "Malware"])
    
# Create columns
col1, col2 = st.columns([2, 1])

with col1:
    st.header("Network Visualization")
    # Create network graph with Plotly
    network = NetworkGraph()
    network.create_small_office_network()
    
    # Create Plotly figure
    fig = create_network_figure(network)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.header("Live Stats")
    
    # Metrics
    metric_col1, metric_col2 = st.columns(2)
    with metric_col1:
        st.metric("Nodes", len(network.nodes))
        st.metric("Active Attacks", 2)
    with metric_col2:
        st.metric("Traffic (Mbps)", "45.2")
        st.metric("Threat Level", "Medium")
    
    # Attack timeline
    st.subheader("Attack Timeline")
    attack_data = pd.DataFrame({
        "time": ["10:00", "10:01", "10:02"],
        "attack": ["Port Scan", "DDoS", "Malware"],
        "severity": ["Low", "High", "Medium"]
    })
    st.dataframe(attack_data)
    
    # Compromised nodes
    st.subheader("Compromised Nodes")
    compromised = [n.name for n in network.nodes.values() if n.is_compromised]
    if compromised:
        for node in compromised[:5]:
            st.error(f"⚠️ {node}")
    else:
        st.success("✅ No compromised nodes")