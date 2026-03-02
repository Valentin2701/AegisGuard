import torch
import torch.nn as nn
import torch.nn.functional as F

class FocalLoss(nn.Module):
    """
    Focal Loss for imbalanced classification
     - alpha: weight for the rare class
     - gamma: focusing parameter to reduce loss for well-classified examples
    """
    def __init__(self, alpha=0.25, gamma=2.0):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        
    def forward(self, inputs, targets):
        ce_loss = F.cross_entropy(inputs, targets, reduction='none')
        pt = torch.exp(-ce_loss)
        focal_loss = self.alpha * (1 - pt) ** self.gamma * ce_loss
        return focal_loss.mean()

class WeightedCrossEntropyLoss(nn.Module):
    """
    Weighted cross-entropy loss
     - class_weights: tensor of shape [num_classes] with weights for each class
    """
    def __init__(self, class_weights=None):
        super().__init__()
        self.class_weights = class_weights
        
    def forward(self, inputs, targets):
        if self.class_weights is not None:
            weights = self.class_weights.to(targets.device)
            return F.cross_entropy(inputs, targets, weight=weights)
        return F.cross_entropy(inputs, targets)