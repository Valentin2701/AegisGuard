#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def quick_test():
    """Quick test of all components"""
    print("🚀 Quick Test - NetSentinel AI")
    
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
        
        # Quick traffic
        traffic = TrafficGenerator(net)
        traffic.create_random_connections(2)
        packets = traffic.generate_packets(1.0)
        print(f"✅ Traffic: {len(packets)} packets")
        
        # Quick attack
        attack = AttackGenerator(net)
        attack.generate_specific_attack(AttackType.PORT_SCAN, 0.5)
        attack_packets = attack.update(1.0)
        print(f"✅ Attacks: {len(attack_packets)} packets")
        
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