import logging
import time

from . import SimulationAdapter, FeatureExtractor, GraphBuilder

# Настройка на логване
logging.basicConfig(level=logging.INFO)

def main():
    adapter = SimulationAdapter(
        socket_host="localhost",
        socket_port=8000,
        rest_api_url="http://localhost:8000/api/v1",
        api_key=None
    )
    
    try:
        adapter.connect()
    except Exception as e:
        print(f"Failed to connect: {e}")
        return
    print("Waiting for data...")
    time.sleep(10)
    
    flows = adapter.get_flows(window_seconds=5)
    print(f"Got {len(flows)} flows in last 5 seconds")
    
    if flows:
        flow = flows[0]
        print(f"Sample flow: {flow.src_ip}:{flow.src_port} -> {flow.dst_ip}:{flow.dst_port}")
        print(f"  Protocol: {flow.protocol}, Bytes: {flow.bytes_sent}, Label: {flow.label}")
    
    status = adapter.get_simulation_status()
    print(f"Simulation status: {status}")
    
    attacks = adapter.get_attack_info()
    print(f"Active attacks: {attacks}")
    
    if flows:
        feature_extractor = FeatureExtractor()
        feature_extractor.fit(flows)
        
        graph_builder = GraphBuilder(feature_extractor)
        graph = graph_builder.build_graph(flows)
        
        print(f"Graph built: {graph}")
        print(f"  Nodes: {graph['ip'].x.shape[0]}")
        print(f"  Edges: {graph['ip', 'communicates', 'ip'].edge_index.shape[1]}")

        adapter.disconnect()

if __name__ == "__main__":
    main()