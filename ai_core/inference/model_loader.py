import pickle
import torch
import yaml
from pathlib import Path
from ..data.preprocessing import GraphBuilder
from ..models.aegis_gnn import AegisGuardGNN

def load_model(model_dir: str):
    model_dir = Path(model_dir)
    
    with open('.' / 'config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    with open(model_dir / 'feature_extractor.pkl', 'rb') as f:
        feature_extractor = pickle.load(f)
    
    graph_builder = GraphBuilder(feature_extractor)
    
    model = AegisGuardGNN(
        node_features=config['model']['node_features'],
        hidden_dim=config['model']['hidden_dim'],
        num_layers=config['model']['num_layers'],
        dropout=config['model']['dropout'],
        num_classes=config['model']['num_classes']
    )
    
    checkpoint = torch.load(model_dir / 'best_model.pt', map_location='cpu')
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    
    return model, feature_extractor, graph_builder, config