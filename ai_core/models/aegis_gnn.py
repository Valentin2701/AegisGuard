import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATConv, SAGEConv, global_mean_pool, global_max_pool
from torch_geometric.nn import BatchNorm

class AegisGuardGNN(nn.Module):
    def __init__(self, 
                 node_features: int,
                 hidden_dim: int = 128,
                 num_layers: int = 3,
                 dropout: float = 0.2,
                 num_classes: int = 2):
        super().__init__()

        self.hidden_dim = hidden_dim
        self.dropout = dropout

        self.node_encoder = nn.Sequential(
            nn.Linear(node_features, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout)
        )

        self.convs = nn.ModuleList()
        self.bns = nn.ModuleList()

        for i in range(num_layers):
            if i == 0:
                self.convs.append(GATConv(hidden_dim, hidden_dim // 4, heads=4, concat=True))
            else:
                self.convs.append(SAGEConv(hidden_dim, hidden_dim))
            self.bns.append(BatchNorm(hidden_dim))

        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, num_classes)
        )

    def forward(self, data):
        x = self.node_encoder(data.x)
        edge_index = data.edge_index

        for i, conv in enumerate(self.convs):
            x = conv(x, edge_index)
            x = self.bns[i](x)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)

        mean_pool = global_mean_pool(x, data.batch)
        max_pool = global_max_pool(x, data.batch)
        graph_embedding = torch.cat([mean_pool, max_pool], dim=1)

        logits = self.classifier(graph_embedding)
        return logits

    def get_embeddings(self, data):
        x = self.node_encoder(data.x)
        edge_index = data.edge_index

        for i, conv in enumerate(self.convs):
            x = conv(x, edge_index)
            x = self.bns[i](x)
            x = F.relu(x)

        mean_pool = global_mean_pool(x, data.batch)
        max_pool = global_max_pool(x, data.batch)
        return torch.cat([mean_pool, max_pool], dim=1)