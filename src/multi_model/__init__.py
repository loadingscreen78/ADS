"""
Multi-Model Ensemble System
Based on: Multi-Model Awareness for Drift Detection

Components:
- Multiple model types (RF, XGBoost, NN, LogReg)
- Cross-model drift detection
- Ensemble predictions
- Model agreement monitoring
"""

from .ensemble import MultiModelEnsemble

__all__ = ['MultiModelEnsemble']
