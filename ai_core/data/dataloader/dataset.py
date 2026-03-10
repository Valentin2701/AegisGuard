import torch
from torch.utils.data import Dataset, DataLoader
from torch_geometric.data import Batch
import numpy as np
from typing import List, Tuple, Optional
import time
from collections import deque
import random

from ..interface import NetworkFlow
from ..preprocessing import FeatureExtractor, GraphBuilder, TemporalWindow

class AegisDataset(Dataset):
    """
    Dataset за обучение на AegisGuard
    Поддържа:
    - Събиране на данни от симулацията
    - Изграждане на графи
    - Балансиране на класовете
    """
    
    def __init__(self, 
                 adapter,
                 feature_extractor: FeatureExtractor,
                 graph_builder: GraphBuilder,
                 window_size: int = 60,
                 stride: int = 10,
                 max_samples: int = 1000,
                 balance_classes: bool = True):
        
        self.adapter = adapter
        self.feature_extractor = feature_extractor
        self.graph_builder = graph_builder
        self.window_size = window_size
        self.stride = stride
        self.max_samples = max_samples
        self.balance_classes = balance_classes
        
        # Буфер за графи
        self.graphs = []
        self.labels = []
        
        # Статистики за класовете
        self.class_counts = {}
        
    def collect_data(self, collection_time: int = 60):
        """
        Takes data from the simulation for a specified duration and builds graphs
        """
        print(f"📊 Collecting data for {collection_time} seconds...")
        
        start_time = time.time()
        flow_buffer = []
        
        while time.time() - start_time < collection_time:
            # Take flows with the adapter
            flows = self.adapter.get_flows(window_seconds=5)
            
            if flows:
                flow_buffer.extend(flows)
                
                # Periodically build graphs from the buffer
                if len(flow_buffer) >= 10:  # Random threshold for building graphs
                    self._build_graphs_from_flows(flow_buffer)
                    flow_buffer = []
            
            time.sleep(1)
        
        # Last graph building for remaining flows
        if flow_buffer:
            self._build_graphs_from_flows(flow_buffer)
        
        print(f"✅ Collected {len(self.graphs)} graphs")
        print(f"📈 Class distribution: {self._get_class_distribution()}")
        
    def _build_graphs_from_flows(self, flows: List[NetworkFlow]):
        """
        Builds graphs from a list of flows and updates the dataset
        """
        # Builds graph
        graph = self.graph_builder.build_graph(flows)
        
        if graph.num_nodes > 0:
            has_attack = any(f.label > 0 for f in flows)
            label = 1 if has_attack else 0
            
        # Save graph and label
        self.graphs.append(graph)
        self.labels.append(label)
            
        # Update class counts
        self.class_counts[label] = self.class_counts.get(label, 0) + 1
            
        while len(self.graphs) > self.max_samples:
            self._trim_dataset()
    
    def _trim_dataset(self):
        """
        Removes oldest samples to maintain max_samples limit, optionally balancing classes
        """
        if self.balance_classes and len(self.class_counts) > 1:
            majority_class = max(self.class_counts, key=self.class_counts.get)
            
            # Remove majority
            indices_to_remove = []
            for i, (graph, label) in enumerate(zip(self.graphs, self.labels)):
                if label == majority_class and len(indices_to_remove) < 10:
                    indices_to_remove.append(i)
            
            # Remove identified samples
            for i in sorted(indices_to_remove, reverse=True):
                self.graphs.pop(i)
                self.labels.pop(i)
                self.class_counts[majority_class] -= 1
        else:
            # Just remove oldest sample
            self.graphs.pop(0)
            old_label = self.labels.pop(0)
            self.class_counts[old_label] -= 1
    
    def _get_class_distribution(self) -> dict:
        """Returns the distribution of classes in the dataset"""
        return {k: v for k, v in self.class_counts.items() if v > 0}
    
    def __len__(self) -> int:
        return len(self.graphs)
    
    def __getitem__(self, idx) -> Tuple:
        return self.graphs[idx], self.labels[idx]

def collate_fn(batch):
    """
    Custom collate function for batching graphs and labels
    """
    graphs = [item[0] for item in batch]
    labels = [item[1] for item in batch]
    
    # Batching graphs with PyG
    batched_graphs = Batch.from_data_list(graphs)
    
    return batched_graphs, torch.tensor(labels)

def create_dataloaders(adapter,
                       feature_extractor,
                       graph_builder,
                       batch_size: int = 32,
                       train_ratio: float = 0.7,
                       val_ratio: float = 0.15,
                       collection_time: int = 300):
    """
    Create train/val/test dataloaders from the simulation data
    """
    # Create dataset
    dataset = AegisDataset(
        adapter=adapter,
        feature_extractor=feature_extractor,
        graph_builder=graph_builder,
        max_samples=2000
    )
    
    # Collect data from the simulation
    dataset.collect_data(collection_time=collection_time)
    
    # Data splitting
    train_size = int(train_ratio * len(dataset))
    val_size = int(val_ratio * len(dataset))
    test_size = len(dataset) - train_size - val_size
    
    train_dataset, val_dataset, test_dataset = torch.utils.data.random_split(
        dataset, [train_size, val_size, test_size]
    )
    
    # Create dataloaders
    train_loader = DataLoader(
        train_dataset, 
        batch_size=batch_size, 
        shuffle=True,
        collate_fn=collate_fn
    )
    
    val_loader = DataLoader(
        val_dataset, 
        batch_size=batch_size, 
        shuffle=False,
        collate_fn=collate_fn
    )
    
    test_loader = DataLoader(
        test_dataset, 
        batch_size=batch_size, 
        shuffle=False,
        collate_fn=collate_fn
    )
    
    return train_loader, val_loader, test_loader