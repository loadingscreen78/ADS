# ML Auto-Retrain System
"""
Automated Machine Learning Retraining System with Predictive Drift Detection

This package provides:
- Drift detection (KS Test + PSI)
- LSTM-based drift prediction
- CARA cost-aware scheduling
- Automated model retraining
- Fairness monitoring
"""

__version__ = "1.0.0"
__author__ = "ML Auto-Retrain Team"

# Import main components for easy access
from src.drift.drift_engine import DriftEngine
from src.retraining.retrain_engine import RetrainEngine
from src.scheduler.cara import CARAScheduler

__all__ = [
    "DriftEngine",
    "RetrainEngine",
    "CARAScheduler",
]
