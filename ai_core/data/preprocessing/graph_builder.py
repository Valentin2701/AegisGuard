from typing import List
import torch
import networkx as nx
from ai_core.data.interface.flow_schema import NetworkFlow
from ai_core.data.preprocessing.feature_extractor import FeatureExtractor
from torch_geometric.data import HeteroData
import numpy as np

class GraphBuilder:
    """
    Builds heterogeneous graphs from flows
    """
    
    def __init__(self, feature_extractor: FeatureExtractor):
        self.feature_extractor = feature_extractor
        self.ip_to_idx = {}
        self.current_idx = 0
        
    def build_graph(self, flows: List[NetworkFlow]) -> HeteroData:
        """
        Convert flows to PyTorch Geometric HeteroData object
        """
        data = HeteroData()
        
        # Reset indices for this graph
        self.ip_to_idx = {}
        self.current_idx = 0
        
        # 1. Extract node features
        node_features = self.feature_extractor.extract_node_features(flows)
        
        # 2. Create IP nodes
        ip_nodes = list(node_features.keys())
        for ip in ip_nodes:
            self.ip_to_idx[ip] = self.current_idx
            self.current_idx += 1
        
        # 3. Add node features to graph
        ip_features = torch.tensor([node_features[ip] for ip in ip_nodes], 
                                    dtype=torch.float)
        data['ip'].x = ip_features
        
        # 4. Create edges (flows) between IPs
        src_indices = []
        dst_indices = []
        edge_features = []
        edge_labels = []
        
        for flow in flows:
            if flow.src_ip in self.ip_to_idx and flow.dst_ip in self.ip_to_idx:
                src_indices.append(self.ip_to_idx[flow.src_ip])
                dst_indices.append(self.ip_to_idx[flow.dst_ip])
                
                # Edge features from flow
                edge_features.append([
                    flow.bytes_sent / 1000,  # Normalize
                    flow.packets,
                    flow.duration,
                    flow.src_port / 65535,  # Normalize port
                    flow.dst_port / 65535,
                    hash(flow.protocol) % 100 / 100  # Simple protocol encoding
                ])
                
                edge_labels.append(flow.label)
        
        # 5. Add edges to graph
        if src_indices:
            data['ip', 'communicates', 'ip'].edge_index = torch.tensor(
                [src_indices, dst_indices], dtype=torch.long
            )
            data['ip', 'communicates', 'ip'].edge_attr = torch.tensor(
                edge_features, dtype=torch.float
            )
            data['ip', 'communicates', 'ip'].y = torch.tensor(
                edge_labels, dtype=torch.long
            )
        
        return data