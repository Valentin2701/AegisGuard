import torch
import torch.optim as optim
from torch.optim.lr_scheduler import ReduceLROnPlateau
import numpy as np
from tqdm import tqdm
import wandb
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

class AegisTrainer:
    """
    Trainer for AegisGuard GNN model
    """
    
    def __init__(self,
                 model,
                 train_loader,
                 val_loader,
                 test_loader,
                 config):
        
        self.model = model
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.test_loader = test_loader
        self.config = config
        
        # Optimizer
        self.optimizer = optim.AdamW(
            model.parameters(),
            lr=config['learning_rate'],
            weight_decay=config['weight_decay']
        )
        
        # Scheduler
        self.scheduler = ReduceLROnPlateau(
            self.optimizer,
            mode='min',
            factor=0.5,
            patience=5,
            verbose=True
        )
        
        # Loss function
        if config.get('use_focal_loss', False):
            from .losses import FocalLoss
            self.criterion = FocalLoss(
                alpha=config.get('focal_alpha', 0.25),
                gamma=config.get('focal_gamma', 2.0)
            )
        else:
            # Calculate class weights for imbalanced data
            class_weights = self._compute_class_weights()
            from .losses import WeightedCrossEntropyLoss
            self.criterion = WeightedCrossEntropyLoss(class_weights)
        
        # Tracking
        self.best_val_loss = float('inf')
        self.patience_counter = 0
        self.current_epoch = 0
        
        # Logging
        self.use_wandb = config.get('use_wandb', False)
        if self.use_wandb:
            wandb.init(project="aegisguard", config=config)
        
    def _compute_class_weights(self):
        """Calculates class weights based on the training dataset labels to handle class imbalance"""
        if not hasattr(self.train_loader.dataset, 'labels'):
            return None
        
        labels = self.train_loader.dataset.labels
        class_counts = np.bincount(labels)
        total = len(labels)
        
        if len(class_counts) > 1:
            weights = total / (len(class_counts) * class_counts)
            return torch.tensor(weights, dtype=torch.float)
        
        return None
    
    def train_epoch(self):
        """One epoch of training"""
        self.model.train()
        total_loss = 0
        all_preds = []
        all_labels = []
        
        pbar = tqdm(self.train_loader, desc=f"Epoch {self.current_epoch + 1} [Train]")
        for batch_idx, (data, labels) in enumerate(pbar):
            self.optimizer.zero_grad()
            
            # Forward pass
            logits = self.model(data)
            loss = self.criterion(logits, labels)
            
            # Backward pass
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            self.optimizer.step()
            
            # Tracking
            total_loss += loss.item()
            preds = logits.argmax(dim=1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            
            # Update progress bar
            pbar.set_postfix({'loss': loss.item()})
        
        # Calculate metrics
        avg_loss = total_loss / len(self.train_loader)
        accuracy = accuracy_score(all_labels, all_preds)
        
        return {
            'train_loss': avg_loss,
            'train_accuracy': accuracy
        }
    
    def validate(self, loader, name='val'):
        """Validation"""
        self.model.eval()
        total_loss = 0
        all_preds = []
        all_labels = []
        
        with torch.no_grad():
            for data, labels in tqdm(loader, desc=f"Epoch {self.current_epoch + 1} [{name}]"):
                logits = self.model(data)
                loss = self.criterion(logits, labels)
                
                total_loss += loss.item()
                preds = logits.argmax(dim=1)
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
        
        # Calculate metrics
        avg_loss = total_loss / len(loader)
        accuracy = accuracy_score(all_labels, all_preds)
        
        # For binary classification, calculate precision, recall, F1. For multi-class, use weighted average
        if len(set(all_labels)) == 2:
            precision = precision_score(all_labels, all_preds, average='binary')
            recall = recall_score(all_labels, all_preds, average='binary')
            f1 = f1_score(all_labels, all_preds, average='binary')
        else:
            precision = precision_score(all_labels, all_preds, average='weighted', zero_division=0)
            recall = recall_score(all_labels, all_preds, average='weighted', zero_division=0)
            f1 = f1_score(all_labels, all_preds, average='weighted', zero_division=0)
        
        return {
            f'{name}_loss': avg_loss,
            f'{name}_accuracy': accuracy,
            f'{name}_precision': precision,
            f'{name}_recall': recall,
            f'{name}_f1': f1
        }
    
    def train(self, num_epochs):
        """Main training loop with early stopping and checkpointing"""
        
        for epoch in range(num_epochs):
            self.current_epoch = epoch
            
            # Training
            train_metrics = self.train_epoch()
            
            # Validation
            val_metrics = self.validate(self.val_loader, 'val')
            
            # Testing (optional)
            if self.test_loader:
                test_metrics = self.validate(self.test_loader, 'test')
            else:
                test_metrics = {}
            
            # Combine metrics for logging
            all_metrics = {**train_metrics, **val_metrics, **test_metrics}
            
            # Logging
            self._log_metrics(all_metrics)
            
            # Scheduler
            self.scheduler.step(val_metrics['val_loss'])
            
            # Checkpoint
            if val_metrics['val_loss'] < self.best_val_loss:
                self.best_val_loss = val_metrics['val_loss']
                self.patience_counter = 0
                self._save_checkpoint()
                print(f"✅ New best model saved!")
            else:
                self.patience_counter += 1
            
            # Early stopping
            if self.patience_counter >= self.config.get('patience', 10):
                print(f"🛑 Early stopping at epoch {epoch + 1}")
                break
            
            print(f"Epoch {epoch + 1}: Loss={train_metrics['train_loss']:.4f}, "
                  f"Val F1={val_metrics['val_f1']:.4f}")
        
        # Final evaluation on test set
        if self.test_loader:
            print("\n📊 Final Test Results:")
            test_metrics = self.validate(self.test_loader, 'test')
            for key, value in test_metrics.items():
                print(f"  {key}: {value:.4f}")
            
            # Visualize confusion matrix
            self._plot_confusion_matrix()
    
    def _log_metrics(self, metrics):
        if self.use_wandb:
            wandb.log(metrics, step=self.current_epoch)
    
    def _save_checkpoint(self):
        checkpoint = {
            'epoch': self.current_epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'best_val_loss': self.best_val_loss,
            'config': self.config
        }
        
        torch.save(checkpoint, 'checkpoints/best_model.pt')
    
    def _plot_confusion_matrix(self):
        """Visualize confusion matrix for the test set"""
        if not self.test_loader:
            return
        
        self.model.eval()
        all_preds = []
        all_labels = []
        
        with torch.no_grad():
            for data, labels in self.test_loader:
                logits = self.model(data)
                preds = logits.argmax(dim=1)
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
        
        cm = confusion_matrix(all_labels, all_preds)
        
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
        plt.title('Confusion Matrix')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.savefig('results/confusion_matrix.png')
        plt.show()