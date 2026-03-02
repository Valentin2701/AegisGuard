import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATConv, SAGEConv, global_mean_pool, global_max_pool
from torch_geometric.nn import BatchNorm

class AegisGuardGNN(nn.Module):
    """
    GNN for graph classification in AegisGuard
    """
    
    def __init__(self, 
                 node_features: int,
                 hidden_dim: int = 128,
                 num_layers: int = 3,
                 dropout: float = 0.2,
                 num_classes: int = 2):
        
        super().__init__()
        
        self.hidden_dim = hidden_dim
        self.dropout = dropout
        
        # Input layer to encode node features
        self.node_encoder = nn.Sequential(
            nn.Linear(node_features, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        
        # GNN слоеве (използваме GAT за attention)
        self.convs = nn.ModuleList()
        self.bns = nn.ModuleList()
        
        for i in range(num_layers):
            if i == 0:
                self.convs.append(GATConv(hidden_dim, hidden_dim // 4, heads=4, concat=True))
            else:
                self.convs.append(SAGEConv(hidden_dim, hidden_dim))
            self.bns.append(BatchNorm(hidden_dim))
        
        # Classififer
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),  # *2 защото конкатенираме mean и max pooling
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, num_classes)
        )
        
    def forward(self, data):
        # 1. Encoding node features
        x = self.node_encoder(data.x)
        
        # 2. GNN layers
        for i, conv in enumerate(self.convs):
            x = conv(x, data.edge_index)
            x = self.bns[i](x)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)
        
        # 3. Graph-level pooling
        # Combine mean and max pooling for richer graph representation
        mean_pool = global_mean_pool(x, data.batch)
        max_pool = global_max_pool(x, data.batch)
        
        # Concatenation
        graph_embedding = torch.cat([mean_pool, max_pool], dim=1)
        
        # 4. Classification
        logits = self.classifier(graph_embedding)
        
        return logits
    
    def get_embeddings(self, data):
        """Extract graph embeddings before the classifier layer"""
        x = self.node_encoder(data.x)
        
        for i, conv in enumerate(self.convs):
            x = conv(x, data.edge_index)
            x = self.bns[i](x)
            x = F.relu(x)
        
        mean_pool = global_mean_pool(x, data.batch)
        max_pool = global_max_pool(x, data.batch)
        
        return torch.cat([mean_pool, max_pool], dim=1)