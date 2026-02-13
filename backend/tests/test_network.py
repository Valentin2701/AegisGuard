#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulation import NetworkGraph, NetworkNode, NetworkEdge, NodeType, OperatingSystem

def test_basic_network():
    print("Testing Network Simulation...")
    
    network = NetworkGraph()
    network.create_small_office_network()
    
    print(f"✅ Network created: {len(network.nodes)} nodes, {len(network.edges)} edges")
    
    # Test that we can access nodes
    web_server = network.get_node("web_server")
    if web_server:
        print(f"✅ Web server found: {web_server.name}")
        print(f"   Security level: {web_server.security_level}")
        print(f"   Services: {web_server.services}")
    
    # Test edge retrieval
    edge = network.get_edge("router_1", "switch_1")
    if edge:
        print(f"✅ Edge found: {edge.source_id} ↔ {edge.target_id}")
        print(f"   Bandwidth: {edge.bandwidth} Mbps")
        print(f"   Protocol: {edge.current_protocol.value if edge.current_protocol else 'None'}")
    
    # Test serialization
    network_dict = network.to_dict()
    print(f"✅ Network serialized: {network_dict['graph_metrics']}")
    
    # Test visualization
    try:
        network.visualize("tests/test_network.png")
        print("✅ Visualization created successfully")
    except Exception as e:
        print(f"Visualization failed: {e}")
    
    return network

def test_edge_operations():
    print("\nTesting Edge Operations...")
    
    network = NetworkGraph()
    
    # Create two test nodes
    node1 = NetworkNode(
        id="test_node_1",
        name="Test Node 1",
        node_type=NodeType.CLIENT,
        os=OperatingSystem.LINUX,
        ip_address="192.168.1.100",
        mac_address="00:11:22:33:44:55"
    )
    
    node2 = NetworkNode(
        id="test_node_2",
        name="Test Node 2",
        node_type=NodeType.SERVER,
        os=OperatingSystem.LINUX,
        ip_address="192.168.1.200",
        mac_address="00:AA:BB:CC:DD:EE"
    )
    
    network.add_node(node1)
    network.add_node(node2)
    
    # Create an edge
    from simulation.network_edge import Protocol
    edge = network.edges[network.generate_random_edge_id()] = NetworkEdge(
        id="test_edge_1",
        source_id="test_node_1",
        target_id="test_node_2",
        bandwidth=1000,
        latency=5,
        supported_protocols=[Protocol.HTTPS, Protocol.SSH],
        current_protocol=Protocol.HTTPS,
        encryption_level=90
    )
    
    edge_data = edge.to_dict()
    edge_data.pop('id', None)
    edge_data.pop('source', None)
    edge_data.pop('target', None)
    network.graph.add_edge(edge.source_id, edge.target_id, **edge_data)
    
    retrieved_edge = network.get_edge("test_node_1", "test_node_2")
    if retrieved_edge:
        print(f"✅ Edge created and retrieved: {retrieved_edge.source_id} → {retrieved_edge.target_id}")
        print(f"   Bandwidth: {retrieved_edge.bandwidth} Mbps")
        print(f"   Security score: {retrieved_edge.get_security_score():.2f}")
    
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("AegisGuard - Network Graph Test")
    print("=" * 50)
    
    network = test_basic_network()
    test_edge_operations()
    
    print("\n" + "=" * 50)
    print("✅ All basic tests completed!")
    print("=" * 50)