from typing import List
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder

from ai_core.data.flow_schema import NetworkFlow

class FeatureExtractor:
    """
    Converts raw flows to feature vectors
    """
    
    def __init__(self):
        self.ip_encoder = LabelEncoder()
        self.port_encoder = LabelEncoder()
        self.protocol_encoder = LabelEncoder()
        self.scaler = StandardScaler()
        self.is_fitted = False
        
    def fit(self, flows: List[NetworkFlow]):
        """Fit encoders on historical data"""
        # Extract categorical values
        ips = []
        ports = []
        protocols = []
        numerical_features = []
        
        for flow in flows:
            ips.extend([flow.src_ip, flow.dst_ip])
            ports.extend([flow.src_port, flow.dst_port])
            protocols.append(flow.protocol)
            numerical_features.append([
                flow.bytes_sent,
                flow.packets,
                flow.duration
            ])
        
        # Fit encoders
        self.ip_encoder.fit(ips)
        self.port_encoder.fit(ports)
        self.protocol_encoder.fit(protocols)
        self.scaler.fit(numerical_features)
        
        self.is_fitted = True
        
    def extract_node_features(self, flows: List[NetworkFlow]) -> dict:
        """Extract features for each node (IP address)"""
        if not self.is_fitted:
            raise ValueError("Must call fit() first")
            
        node_features = {}
        
        # Group flows by IP
        for flow in flows:
            for ip in [flow.src_ip, flow.dst_ip]:
                if ip not in node_features:
                    node_features[ip] = {
                        'bytes_sent': [],
                        'packets': [],
                        'unique_dsts': set(),
                        'unique_ports': set()
                    }
                
                if ip == flow.src_ip:
                    node_features[ip]['bytes_sent'].append(flow.bytes_sent)
                    node_features[ip]['packets'].append(flow.packets)
                    node_features[ip]['unique_dsts'].add(flow.dst_ip)
                    node_features[ip]['unique_ports'].add(flow.dst_port)
        
        # Aggregate features
        feature_vectors = {}
        for ip, features in node_features.items():
            feature_vectors[ip] = np.array([
                np.mean(features['bytes_sent']) if features['bytes_sent'] else 0,
                np.std(features['bytes_sent']) if len(features['bytes_sent']) > 1 else 0,
                np.mean(features['packets']) if features['packets'] else 0,
                len(features['unique_dsts']),
                len(features['unique_ports'])
            ])
        
        return feature_vectors