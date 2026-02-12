#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def quick_test():
    """Quick test of all components"""
    print("🚀 Quick Test - AegisGuard")
    
    try:
        from simulation import (
            NetworkGraph, TrafficGenerator, AttackGenerator,
            TrafficPattern, AttackType
        )
        print("✅ Imports successful")
        
        # Quick network
        net = NetworkGraph()
        net.create_small_office_network()
        print(f"✅ Network: {len(net.nodes)} nodes")
        
        # Quick traffic - use methods you actually have
        traffic = TrafficGenerator(net)
        
        # Create specific connections (not random ones)
        connections_created = 0
        
        # Try to create a web browsing connection
        if "client_1" in net.nodes and "web_server" in net.nodes:
            conn = traffic.create_connection(
                source_id="client_1",
                destination_id="web_server",
                pattern=TrafficPattern.WEB_BROWSING
            )
            if conn:
                connections_created += 1
                print(f"✅ Created web browsing connection")
        
        # Try to create a database connection
        if "client_2" in net.nodes and "db_server" in net.nodes:
            conn = traffic.create_connection(
                source_id="client_2",
                destination_id="db_server",
                pattern=TrafficPattern.DATABASE
            )
            if conn:
                connections_created += 1
                print(f"✅ Created database connection")
        
        # Generate some traffic
        packets = traffic.generate_packets(time_delta=1.0)
        print(f"✅ Traffic: {len(packets)} packets generated")
        print(f"   Active connections: {connections_created}")
        
        # Quick attack
        attack = AttackGenerator(net)
        attack_gen = attack.generate_specific_attack(AttackType.PORT_SCAN, 0.5)
        
        if attack_gen:
            print(f"✅ Created {attack_gen.attack_type.value} attack")
            print(f"   Source: {attack_gen.source_id}")
            print(f"   Target: {attack_gen.target_id}")
        
        attack_packets = attack.update(time_delta=1.0)
        print(f"✅ Attacks: {len(attack_packets)} attack packets")
        
        # Get some stats
        traffic_stats = traffic.get_traffic_stats()
        attack_stats = attack.get_stats()
        
        print(f"\n📊 Traffic Stats:")
        print(f"   Total packets: {traffic_stats.get('total_packets', 0)}")
        print(f"   Total bytes: {traffic_stats.get('total_bytes', 0):,}")
        
        print(f"\n📊 Attack Stats:")
        print(f"   Active attacks: {attack_stats.get('active_attacks', 0)}")
        print(f"   Detected attacks: {attack_stats.get('detected_attacks', 0)}")
        
        print("\n🎉 All quick tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)