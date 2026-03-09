import time
import yaml
from .data.interface import SimulationAdapter
from .data.preprocessing import FeatureExtractor, GraphBuilder
from .data.dataloader import create_dataloaders
from .models import AegisGuardGNN
from .training import AegisTrainer

def main():
    # Load configuration
    with open('ai_core/config/training_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # 1. Connect to simulation
    print("🔄 Connecting to simulation...")
    adapter = SimulationAdapter(
        socket_host="localhost",
        socket_port=8000,
        rest_api_url="http://localhost:8000/api/v1"
    )
    adapter.connect()
    
    # 2. Initialize feature extractor and graph builder
    feature_extractor = FeatureExtractor()
    graph_builder = GraphBuilder(feature_extractor)
    
    # 3. Collect initial data for fitting the feature extractor
    print("📊 Collecting initial data for fitting...")
    initial_flows = []
    for _ in range(5):
        flows = adapter.get_flows(window_seconds=10)
        if flows:
            initial_flows.extend(flows)
        time.sleep(1)
    
    # Fit feature extractor
    feature_extractor.fit(initial_flows)
    print(f"✅ Feature extractor fitted on {len(initial_flows)} flows")
    
    # 4. Create dataloaders
    train_loader, val_loader, test_loader = create_dataloaders(
        adapter=adapter,
        feature_extractor=feature_extractor,
        graph_builder=graph_builder,
        batch_size=config['training']['batch_size'],
        collection_time=config['data']['collection_time']
    )
    
    # 5. Create model
    model = AegisGuardGNN(
        node_features=5,
        hidden_dim=config['model']['hidden_dim'],
        num_layers=config['model']['num_layers'],
        dropout=config['model']['dropout'],
        num_classes=2
    )
    
    print(f"✅ Model created with {sum(p.numel() for p in model.parameters())} parameters")
    
    # 6. Trainer
    trainer = AegisTrainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        test_loader=test_loader,
        config=config['training']
    )
    
    # 7. Train
    print("\n🎯 Starting training...")
    trainer.train(num_epochs=config['training']['num_epochs'])
    
    # 8. Disconnect from simulation
    adapter.disconnect()
    print("✅ Training complete!")

if __name__ == "__main__":
    main()