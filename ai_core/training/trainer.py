# aegisguard/training/trainer.py
import torch
import torch.optim as optim
from torch.optim.lr_scheduler import ReduceLROnPlateau
import numpy as np
from tqdm import tqdm
import wandb
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import time
import os

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
            patience=5
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
            if class_weights is not None:
                from .losses import WeightedCrossEntropyLoss
                self.criterion = WeightedCrossEntropyLoss(class_weights)
            else:
                self.criterion = torch.nn.CrossEntropyLoss()
        
        # Tracking
        self.best_val_loss = float('inf')
        self.patience_counter = 0
        self.current_epoch = 0
        
        # Logging
        self.use_wandb = config.get('use_wandb', False)
        if self.use_wandb:
            wandb.init(project="aegisguard", config=config)
        
        # Създаване на директории
        os.makedirs('checkpoints', exist_ok=True)
        os.makedirs('results', exist_ok=True)
        
        print(f"✅ Trainer initialized with {len(train_loader)} train batches, "
              f"{len(val_loader)} val batches")
    
    def _compute_class_weights(self):
        """Compute class weights based on the training dataset for imbalanced classification"""
        try:
            if not hasattr(self.train_loader.dataset, 'labels'):
                return None
            
            # Take labels from the original dataset if using Subset
            if hasattr(self.train_loader.dataset, 'dataset'):
                labels = [self.train_loader.dataset.dataset.labels[i] 
                         for i in self.train_loader.dataset.indices]
            else:
                labels = self.train_loader.dataset.labels
            
            class_counts = np.bincount(labels)
            total = len(labels)
            
            if len(class_counts) > 1 and min(class_counts) > 0:
                weights = total / (len(class_counts) * class_counts)
                print(f"📊 Class weights: {weights}")
                return torch.tensor(weights, dtype=torch.float)
            
            return None
        except Exception as e:
            print(f"⚠️ Could not compute class weights: {e}")
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
            pbar.set_postfix({'loss': f'{loss.item():.4f}'})
        
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
        avg_loss = total_loss / len(loader) if len(loader) > 0 else 0
        accuracy = accuracy_score(all_labels, all_preds)
        
        # For binary classification, calculate precision, recall, f1. For multi-class, calculate weighted average
        try:
            if len(set(all_labels)) == 2:
                precision = precision_score(all_labels, all_preds, average='binary', zero_division=0)
                recall = recall_score(all_labels, all_preds, average='binary', zero_division=0)
                f1 = f1_score(all_labels, all_preds, average='binary', zero_division=0)
            else:
                precision = precision_score(all_labels, all_preds, average='weighted', zero_division=0)
                recall = recall_score(all_labels, all_preds, average='weighted', zero_division=0)
                f1 = f1_score(all_labels, all_preds, average='weighted', zero_division=0)
        except Exception as e:
            print(f"⚠️ Could not compute precision/recall/f1: {e}")
            precision = recall = f1 = 0.0
        
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
            epoch_start_time = time.time()
            
            # Training
            train_metrics = self.train_epoch()
            
            # Validation
            val_metrics = self.validate(self.val_loader, 'val')
            
            # Test (every 5 epochs to save time, can be adjusted)
            if self.test_loader and epoch % 5 == 0: 
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
                print(f"  ✅ New best model saved! (val_loss: {self.best_val_loss:.4f})")
            else:
                self.patience_counter += 1
            
            # Early stopping
            if self.patience_counter >= self.config.get('patience', 10):
                print(f"\n🛑 Early stopping at epoch {epoch + 1}")
                break
            
            epoch_time = time.time() - epoch_start_time
            print(f"\nEpoch {epoch + 1}/{num_epochs} "
                  f"({epoch_time:.2f}s): "
                  f"Loss={train_metrics['train_loss']:.4f}, "
                  f"Acc={train_metrics['train_accuracy']:.4f}, "
                  f"Val Loss={val_metrics['val_loss']:.4f}, "
                  f"Val F1={val_metrics['val_f1']:.4f}")
            
            # Current learning rate and patience
            current_lr = self.optimizer.param_groups[0]['lr']
            print(f"  LR: {current_lr:.6f}, Patience: {self.patience_counter}/{self.config.get('patience', 10)}")
        
        # Final evaluation on test set
        if self.test_loader:
            print("\n📊 Final Test Results:")
            test_metrics = self.validate(self.test_loader, 'test')
            for key, value in test_metrics.items():
                print(f"  {key}: {value:.4f}")
            
            # Visualize confusion matrix
            self._plot_confusion_matrix()
        
        # Save final model
        self._save_checkpoint(final=True)
        print(f"\n✅ Training complete! Best val_loss: {self.best_val_loss:.4f}")
    
    def _log_metrics(self, metrics):
        if self.use_wandb:
            wandb.log(metrics, step=self.current_epoch)
    
    def _save_checkpoint(self, final=False):
        checkpoint = {
            'epoch': self.current_epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'best_val_loss': self.best_val_loss,
            'config': self.config
        }
        
        filename = 'checkpoints/best_model.pt' if not final else 'checkpoints/final_model.pt'
        torch.save(checkpoint, filename)
    
    def _plot_confusion_matrix(self):
        """Visualize confusion matrix for the test set"""
        if not self.test_loader:
            return
        
        self.model.eval()
        all_preds = []
        all_labels = []
        
        with torch.no_grad():
            for data, labels in tqdm(self.test_loader, desc="Generating confusion matrix"):
                logits = self.model(data)
                preds = logits.argmax(dim=1)
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
        
        cm = confusion_matrix(all_labels, all_preds)
        
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
        plt.title('Confusion Matrix - AegisGuard')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        
        # Add labels
        label_names = ['Normal', 'Attack']
        tick_marks = np.arange(len(label_names)) + 0.5
        plt.xticks(tick_marks, label_names)
        plt.yticks(tick_marks, label_names)
        
        plt.tight_layout()
        plt.savefig('results/confusion_matrix.png', dpi=150)
        print("📊 Confusion matrix saved to results/confusion_matrix.png")
        plt.show()