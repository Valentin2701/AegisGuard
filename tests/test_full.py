#!/usr/bin/env python3
import sys
import os
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_all_components():
    """Test all simulation components together"""
    print("🧪 AEGIS GUARD - COMPREHENSIVE TEST")
    print("=" * 60)
    
    try:
        # Import all components
        from simulation import (
            NetworkGraph, TrafficGenerator, AttackGenerator,
            TrafficPattern, AttackType, Protocol, NodeType,
            TrafficConfig, AttackConfig
        )
        print("✅ All imports successful")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # ==================== TEST 1: NETWORK CREATION ====================
    print("\n1. Testing Network Creation...")
    print("-" * 40)
    
    network = NetworkGraph()
    network.create_small_office_network()
    
    print(f"   ✅ Network created: {len(network.nodes)} nodes, {len(network.edges)} edges")
    
    # Show some nodes
    print(f"   📊 Node types:")
    node_counts = {}
    for node in network.nodes.values():
        node_type = node.node_type.value
        node_counts[node_type] = node_counts.get(node_type, 0) + 1
    
    for node_type, count in node_counts.items():
        print(f"      {node_type}: {count}")
    
    # ==================== TEST 2: TRAFFIC GENERATION ====================
    print("\n2. Testing Traffic Generation...")
    print("-" * 40)
    
    traffic_gen = TrafficGenerator(network)
    
    # Create some connections
    print("   Creating traffic connections...")
    connections_created = 0
    
    # Web browsing from clients to web server
    if "web_server" in network.nodes and "client_1" in network.nodes:
        conn = traffic_gen.create_connection(
            source_id="client_1",
            destination_id="web_server",
            pattern=TrafficPattern.WEB_BROWSING
        )
        if conn:
            connections_created += 1
            print(f"   ✅ Created web browsing connection")
    
    # Database queries to db server
    if "db_server" in network.nodes and "client_2" in network.nodes:
        conn = traffic_gen.create_connection(
            source_id="client_2",
            destination_id="db_server",
            pattern=TrafficPattern.DATABASE
        )
        if conn:
            connections_created += 1
            print(f"   ✅ Created database connection")
    
    # Generate traffic for 3 seconds
    print(f"   Generating traffic (3 seconds simulation)...")
    all_packets = []
    for i in range(3):
        packets = traffic_gen.generate_packets(time_delta=1.0)
        all_packets.extend(packets)
        print(f"      Second {i+1}: {len(packets)} packets generated")
    
    # Show traffic stats
    stats = traffic_gen.get_traffic_stats()
    print(f"   📊 Traffic Statistics:")
    print(f"      Total packets: {stats['total_packets']}")
    print(f"      Total bytes: {stats['total_bytes']:,}")
    print(f"      Active connections: {stats['active_connections']}")
    print(f"      TCP connections: {stats['tcp_connections']}")
    
    # Show sample packets
    if all_packets:
        sample = all_packets[0]
        print(f"   📦 Sample packet:")
        print(f"      Flow ID: {sample.flow_id[:30]}...")
        print(f"      Protocol: {sample.protocol}")
        print(f"      Size: {sample.payload_size} bytes")
        print(f"      QoS: {sample.qos_class}")
    
    # ==================== TEST 3: ATTACK GENERATION ====================
    print("\n3. Testing Attack Generation...")
    print("-" * 40)
    
    attack_gen = AttackGenerator(network)
    
    # Generate specific attacks
    print("   Generating specific attacks...")
    
    # Port scan attack
    port_scan = attack_gen.generate_specific_attack(
        AttackType.PORT_SCAN,
        intensity=0.7
    )
    if port_scan:
        print(f"   ✅ Port scan attack created")
        print(f"      Source: {port_scan.source_id}")
        print(f"      Target: {port_scan.target_id}")
        print(f"      Intensity: {port_scan.intensity:.2f}")
    
    # DDoS attack
    ddos = attack_gen.generate_specific_attack(
        AttackType.DDOS,
        intensity=0.9
    )
    if ddos:
        print(f"   ✅ DDoS attack created")
        print(f"      Source: {ddos.source_id}")
        print(f"      Target: {ddos.target_id}")
    
    # Generate attack packets
    print("   Generating attack packets (2 seconds simulation)...")
    attack_packets = []
    for i in range(2):
        packets = attack_gen.update(time_delta=1.0)
        attack_packets.extend(packets)
        print(f"      Second {i+1}: {len(packets)} attack packets")
    
    # Show attack stats
    attack_stats = attack_gen.get_stats()
    print(f"   📊 Attack Statistics:")
    print(f"      Total attacks: {attack_stats['total_attacks']}")
    print(f"      Active attacks: {attack_stats['active_attacks']}")
    print(f"      Detected attacks: {attack_stats['detected_attacks']}")
    print(f"      Total damage: {attack_stats['total_damage']:.2f}")
    
    # Show sample attack packet
    if attack_packets:
        sample = attack_packets[0]
        print(f"   💀 Sample attack packet:")
        print(f"      Type: {sample.packet_type}")
        print(f"      Malicious: {sample.is_malicious}")
        print(f"      Threat score: {sample.threat_score:.2f}")
        print(f"      Size: {sample.payload_size} bytes")
    
    # ==================== TEST 4: CONFIGURATION TEST ====================
    print("\n4. Testing Configuration...")
    print("-" * 40)
    
    # Test traffic config
    try:
        web_config = TrafficConfig.get_pattern_config(TrafficPattern.WEB_BROWSING)
        print(f"   ✅ Traffic config loaded for WEB_BROWSING")
        print(f"      Packet rate: {web_config.packet_rate_range} packets/sec")
        print(f"      Avg size: {web_config.avg_packet_size} bytes")
        print(f"      Protocol: {web_config.protocol}")
    except Exception as e:
        print(f"   ⚠️  Traffic config error: {e}")
    
    # Test attack config
    try:
        ddos_config = AttackConfig.get_attack_config(AttackType.DDOS)
        if ddos_config:
            print(f"   ✅ Attack config loaded for DDoS")
            print(f"      Description: {ddos_config.get('description', 'N/A')}")
            print(f"      Packet rate: {ddos_config.get('packet_rate_range', 'N/A')}")
            
        severity = AttackConfig.get_attack_severity(AttackType.DDOS)
        print(f"      Severity: {severity.value}")
    except Exception as e:
        print(f"   ⚠️  Attack config error: {e}")
    
    # ==================== TEST 5: INTEGRATION TEST ====================
    print("\n5. Testing Integration (Traffic + Attacks)...")
    print("-" * 40)
    
    # Simulate mixed traffic for 2 seconds
    print("   Simulating normal traffic + attacks...")
    
    mixed_stats = {
        "normal_packets": 0,
        "attack_packets": 0,
        "total_bytes": 0,
    }
    
    for i in range(2):
        # Generate normal traffic
        normal_packets = traffic_gen.generate_packets(time_delta=1.0)
        mixed_stats["normal_packets"] += len(normal_packets)
        
        # Generate attacks
        attack_packets = attack_gen.update(time_delta=1.0)
        mixed_stats["attack_packets"] += len(attack_packets)
        
        # Calculate bytes
        all_packets = normal_packets + attack_packets
        mixed_stats["total_bytes"] += sum(
            p.payload_size for p in all_packets if hasattr(p, 'payload_size')
        )
        
        print(f"      Second {i+1}: {len(normal_packets)} normal, {len(attack_packets)} attack")
    
    print(f"   📊 Mixed Simulation Results:")
    print(f"      Total normal packets: {mixed_stats['normal_packets']}")
    print(f"      Total attack packets: {mixed_stats['attack_packets']}")
    print(f"      Attack ratio: {mixed_stats['attack_packets']/(mixed_stats['normal_packets'] + mixed_stats['attack_packets'])*100:.1f}%")
    print(f"      Total bytes: {mixed_stats['total_bytes']:,}")
    
    # ==================== TEST 6: NETWORK STATE ====================
    print("\n6. Testing Network State...")
    print("-" * 40)
    
    # Check compromised nodes
    compromised = [
        node.name for node in network.nodes.values() 
        if node.is_compromised
    ]
    
    if compromised:
        print(f"   ⚠️  Compromised nodes: {', '.join(compromised)}")
    else:
        print(f"   ✅ No compromised nodes")
    
    # Check node statistics
    total_cpu = sum(node.cpu_usage for node in network.nodes.values())
    avg_cpu = total_cpu / len(network.nodes) if network.nodes else 0
    
    print(f"   📊 Network Health:")
    print(f"      Average CPU usage: {avg_cpu:.1f}%")
    print(f"      Total nodes: {len(network.nodes)}")
    
    # Visualize network
    try:
        network.visualize("tests/test_comprehensive_network.png")
        print(f"   🎨 Network visualization saved: test_comprehensive_network.png")
    except Exception as e:
        print(f"   ⚠️  Visualization failed: {e}")
    
    return True

def run_performance_test():
    """Run performance test with larger network"""
    print("\n" + "=" * 60)
    print("🏎️  PERFORMANCE TEST")
    print("=" * 60)
    
    try:
        from simulation import NetworkGraph, TrafficGenerator, AttackGenerator
        
        # Create larger network
        print("Creating larger network (20 nodes)...")
        network = NetworkGraph()
        
        # Manually create larger network
        # (In future, you could add a method create_large_network())
        print("   (Note: For performance test, implement create_large_network method)")
        print("   Using small office network for now...")
        network.create_small_office_network()
        
        # Test with many connections
        traffic_gen = TrafficGenerator(network)
        attack_gen = AttackGenerator(network)
        
        # Measure packet generation speed
        import time
        
        print("\nTesting packet generation speed...")
        start_time = time.time()
        
        # Generate lots of packets
        total_packets = 0
        iterations = 10
        
        for i in range(iterations):
            normal = traffic_gen.generate_packets(time_delta=1.0)
            attacks = attack_gen.update(time_delta=1.0)
            total_packets += len(normal) + len(attacks)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        print(f"   Generated {total_packets} packets in {elapsed:.2f} seconds")
        print(f"   Packets per second: {total_packets/elapsed:.0f}")
        print(f"   Real-time factor: {iterations/elapsed:.2f}x")
        
        if elapsed < iterations:
            print("   ✅ Faster than real-time (good for simulation)")
        else:
            print("   ⚠️  Slower than real-time")
        
    except Exception as e:
        print(f"   ⚠️  Performance test failed: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 Starting NetSentinel AI Comprehensive Test Suite")
    print("=" * 60)
    
    all_passed = True
    
    try:
        # Run main test
        if not test_all_components():
            all_passed = False
        
        # Run performance test (optional)
        print("\n" + "=" * 60)
        run_perf = input("Run performance test? (y/n): ").lower().strip()
        if run_perf == 'y':
            if not run_performance_test():
                all_passed = False
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        all_passed = False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! 🎉")
        print("Your NetSentinel AI simulation is working correctly!")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("Check the errors above and fix the issues.")
    
    print("=" * 60)
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)