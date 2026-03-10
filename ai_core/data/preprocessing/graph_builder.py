from typing import List
import torch
import networkx as nx
from ..interface import NetworkFlow
from ..preprocessing import FeatureExtractor
from torch_geometric.data import Data, HeteroData
import numpy as np

class GraphBuilder:
    """
    Builds heterogeneous graphs from flows
    """
    
    def __init__(self, feature_extractor: FeatureExtractor):
        self.feature_extractor = feature_extractor
        self.ip_to_idx = {}
        self.current_idx = 0
        
    def build_graph(self, flows: List[NetworkFlow]) -> Data:
        self.ip_to_idx = {}
        self.current_idx = 0

        # 1. Extract node features
        node_features = self.feature_extractor.extract_node_features(flows)

        # 2. Create IP nodes
        ip_nodes = list(node_features.keys())
        for ip in ip_nodes:
            self.ip_to_idx[ip] = self.current_idx
            self.current_idx += 1

        # 3. Prepare node features tensor
        x = torch.tensor(np.array([node_features[ip] for ip in ip_nodes]), dtype=torch.float)

        # 4. Create edges (flows) between IPs
        src_indices = []
        dst_indices = []
        edge_features = []
        edge_labels = []

        for flow in flows:
            if flow.src_ip in self.ip_to_idx and flow.dst_ip in self.ip_to_idx:
                src_indices.append(self.ip_to_idx[flow.src_ip])
                dst_indices.append(self.ip_to_idx[flow.dst_ip])
                edge_features.append([
                    flow.bytes_sent / 1000,
                    flow.packets_sent / 100,
                    flow.duration,
                    flow.src_port / 65535,
                    flow.dst_port / 65535,
                    hash(flow.protocol) % 100 / 100
                ])
                edge_labels.append(flow.label)

        # Edge index
        edge_index = torch.tensor([src_indices, dst_indices], dtype=torch.long)

        # Create Data object
        data = Data(x=x, edge_index=edge_index)

        if edge_features:
            data.edge_attr = torch.tensor(edge_features, dtype=torch.float)

        return data