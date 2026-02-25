import logging
import time
from data.interface.simulation_adapter import SimulationAdapter
from data.preprocessing.feature_extractor import FeatureExtractor
from data.preprocessing.graph_builder import GraphBuilder

# Настройка на логване
logging.basicConfig(level=logging.INFO)

def main():
    # 1. Създаване на адаптер
    adapter = SimulationAdapter(
        socket_host="localhost",
        socket_port=9999,
        rest_api_url="http://localhost:8000/api",
        api_key=None  # или "your-key"
    )
    
    # 2. Свързване
    try:
        adapter.connect()
    except Exception as e:
        print(f"Failed to connect: {e}")
        return
    
    # 3. Изчакваме малко за да се напълни буфера
    print("Waiting for data...")
    time.sleep(10)
    
    # 4. Вземане на flows
    flows = adapter.get_flows(window_seconds=5)
    print(f"Got {len(flows)} flows in last 5 seconds")
    
    if flows:
        # Примерен flow
        flow = flows[0]
        print(f"Sample flow: {flow.src_ip}:{flow.src_port} -> {flow.dst_ip}:{flow.dst_port}")
        print(f"  Protocol: {flow.protocol}, Bytes: {flow.bytes_sent}, Label: {flow.label}")
    
    # 5. Проверка на статус
    status = adapter.get_simulation_status()
    print(f"Simulation status: {status}")
    
    # 6. Вземане на информация за атаки
    attacks = adapter.get_attack_info()
    print(f"Active attacks: {attacks}")
    
    # 7. Тест на FeatureExtractor и GraphBuilder
    if flows:
        feature_extractor = FeatureExtractor()
        feature_extractor.fit(flows)
        
        graph_builder = GraphBuilder(feature_extractor)
        graph = graph_builder.build_graph(flows)
        
        print(f"Graph built: {graph}")
        print(f"  Nodes: {graph['ip'].x.shape[0]}")
        print(f"  Edges: {graph['ip', 'communicates', 'ip'].edge_index.shape[1]}")
    
    # 8. Затваряне
    adapter.disconnect()

if __name__ == "__main__":
    main()