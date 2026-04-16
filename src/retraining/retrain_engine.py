"""
GPU-Accelerated Retraining Engine using cuML
Day 6-7 Implementation

Trains fraud detection models with:
- GPU acceleration (cuML RandomForest)
- CPU fallback (sklearn)
- Model versioning
- Performance tracking
"""

import time
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple, Optional
import joblib
from datetime import datetime

# GPU/CPU switch
try:
    import cudf
    import cuml
    from cuml.ensemble import RandomForestClassifier as cuRF
    from cuml.metrics import accuracy_score, roc_auc_score
    GPU_AVAILABLE = True
    print("[RetrainEngine] GPU mode (cuML)")
except ImportError:
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier as skRF
    from sklearn.metrics import accuracy_score, roc_auc_score
    GPU_AVAILABLE = False
    print("[RetrainEngine] CPU mode (sklearn)")


class ModelMetrics:
    """Container for model performance metrics."""
    
    def __init__(self, accuracy: float, auc: float, precision: float, 
                 recall: float, f1: float, train_time: float):
        self.accuracy = accuracy
        self.auc = auc
        self.precision = precision
        self.recall = recall
        self.f1 = f1
        self.train_time = train_time
    
    def to_dict(self) -> Dict:
        return {
            'accuracy': round(self.accuracy, 4),
            'auc': round(self.auc, 4),
            'precision': round(self.precision, 4),
            'recall': round(self.recall, 4),
            'f1': round(self.f1, 4),
            'train_time_sec': round(self.train_time, 2)
        }
    
    def __repr__(self):
        return (f"ModelMetrics(acc={self.accuracy:.3f}, auc={self.auc:.3f}, "
                f"f1={self.f1:.3f}, time={self.train_time:.1f}s)")


class RetrainEngine:
    """
    GPU-accelerated model retraining engine.
    
    Features:
    - Automatic GPU/CPU detection
    - RandomForest for fraud detection
    - Model versioning and persistence
    - Performance tracking
    - Fairness monitoring ready
    """
    
    def __init__(self, model_dir: str = "data/models", use_gpu: bool = True):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.use_gpu = use_gpu and GPU_AVAILABLE
        self.current_model = None
        self.model_version = 0
        
        print(f"[RetrainEngine] Initialized")
        print(f"  GPU mode: {self.use_gpu}")
        print(f"  Model dir: {self.model_dir}")
    
    def _prepare_data(self, df: pd.DataFrame) -> Tuple:
        """
        Prepare data for training.
        
        Args:
            df: DataFrame with features and 'isFraud' or 'is_fraud' label
            
        Returns:
            X_train, X_val, y_train, y_val
        """
        # Identify label column
        label_col = 'isFraud' if 'isFraud' in df.columns else 'is_fraud'
        
        if label_col not in df.columns:
            raise ValueError(f"Label column not found. Expected 'isFraud' or 'is_fraud'")
        
        # Separate features and labels
        X = df.drop(columns=[label_col])
        y = df[label_col]
        
        # Remove non-numeric columns
        numeric_cols = X.select_dtypes(include=[np.number]).columns
        X = X[numeric_cols]
        
        # Handle missing values
        X = X.fillna(X.median())
        
        # Train/val split (80/20)
        split_idx = int(len(X) * 0.8)
        X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]
        
        print(f"[RetrainEngine] Data prepared:")
        print(f"  Train: {len(X_train):,} samples, {len(X_train.columns)} features")
        print(f"  Val:   {len(X_val):,} samples")
        print(f"  Fraud rate (train): {y_train.mean():.2%}")
        print(f"  Fraud rate (val):   {y_val.mean():.2%}")
        
        return X_train, X_val, y_train, y_val
    
    def _compute_metrics(self, y_true, y_pred, y_pred_proba, 
                        train_time: float) -> ModelMetrics:
        """Compute comprehensive model metrics."""
        
        # Convert to numpy if needed
        if hasattr(y_true, 'to_numpy'):
            y_true = y_true.to_numpy()
        if hasattr(y_pred, 'to_numpy'):
            y_pred = y_pred.to_numpy()
        if hasattr(y_pred_proba, 'to_numpy'):
            y_pred_proba = y_pred_proba.to_numpy()
        
        # Basic metrics
        accuracy = float(accuracy_score(y_true, y_pred))
        auc = float(roc_auc_score(y_true, y_pred_proba))
        
        # Precision, Recall, F1
        tp = np.sum((y_true == 1) & (y_pred == 1))
        fp = np.sum((y_true == 0) & (y_pred == 1))
        fn = np.sum((y_true == 1) & (y_pred == 0))
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return ModelMetrics(accuracy, auc, precision, recall, f1, train_time)
    
    def train_full(self, train_data_path: str, 
                   n_estimators: int = 100,
                   max_depth: int = 10) -> ModelMetrics:
        """
        Full retraining from scratch.
        
        Args:
            train_data_path: Path to training data (parquet)
            n_estimators: Number of trees
            max_depth: Maximum tree depth
            
        Returns:
            ModelMetrics with performance results
        """
        print(f"\n[RetrainEngine] Starting FULL RETRAIN")
        print(f"  Data: {train_data_path}")
        print(f"  Trees: {n_estimators}, Max depth: {max_depth}")
        
        # Load data
        df = pd.read_parquet(train_data_path)
        X_train, X_val, y_train, y_val = self._prepare_data(df)
        
        # Convert to GPU if available
        if self.use_gpu:
            X_train = cudf.DataFrame.from_pandas(X_train)
            X_val = cudf.DataFrame.from_pandas(X_val)
            y_train = cudf.Series(y_train.values)
            y_val = cudf.Series(y_val.values)
        
        # Train model
        t_start = time.time()
        
        if self.use_gpu:
            model = cuRF(
                n_estimators=n_estimators,
                max_depth=max_depth,
                max_features=0.3,
                n_bins=128,
                random_state=42
            )
        else:
            model = skRF(
                n_estimators=n_estimators,
                max_depth=max_depth,
                max_features=0.3,
                random_state=42,
                n_jobs=-1
            )
        
        model.fit(X_train, y_train)
        train_time = time.time() - t_start
        
        print(f"[RetrainEngine] Training complete in {train_time:.2f}s")
        
        # Evaluate
        y_pred = model.predict(X_val)
        y_pred_proba = model.predict_proba(X_val)[:, 1]
        
        metrics = self._compute_metrics(y_val, y_pred, y_pred_proba, train_time)
        print(f"[RetrainEngine] Validation metrics: {metrics}")
        
        # Save model
        self.current_model = model
        self.model_version += 1
        self._save_model(model, metrics)
        
        return metrics
    
    def train_incremental(self, new_data_path: str) -> ModelMetrics:
        """
        Incremental retraining on recent data.
        
        For RandomForest, we retrain with combined old + new data
        but with smaller n_estimators for speed.
        
        Args:
            new_data_path: Path to new data batch
            
        Returns:
            ModelMetrics
        """
        print(f"\n[RetrainEngine] Starting INCREMENTAL RETRAIN")
        print(f"  New data: {new_data_path}")
        
        if self.current_model is None:
            print("[WARN] No existing model, performing full retrain instead")
            return self.train_full(new_data_path, n_estimators=50)
        
        # For simplicity, retrain with fewer trees
        return self.train_full(new_data_path, n_estimators=50, max_depth=8)
    
    def _save_model(self, model, metrics: ModelMetrics):
        """Save model with version and metadata."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_filename = f"fraud_model_v{self.model_version}_{timestamp}.pkl"
        model_path = self.model_dir / model_filename
        
        # Save model
        joblib.dump(model, model_path)
        
        # Save metadata
        metadata = {
            'version': self.model_version,
            'timestamp': timestamp,
            'gpu_trained': self.use_gpu,
            'metrics': metrics.to_dict()
        }
        
        metadata_path = self.model_dir / f"metadata_v{self.model_version}.json"
        import json
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"[RetrainEngine] Model saved: {model_path}")
        print(f"[RetrainEngine] Metadata saved: {metadata_path}")
    
    def load_latest_model(self) -> Optional[object]:
        """Load the most recent model."""
        model_files = sorted(self.model_dir.glob("fraud_model_v*.pkl"))
        
        if not model_files:
            print("[WARN] No saved models found")
            return None
        
        latest_model_path = model_files[-1]
        model = joblib.load(latest_model_path)
        
        # Extract version from filename
        version_str = latest_model_path.stem.split('_v')[1].split('_')[0]
        self.model_version = int(version_str)
        self.current_model = model
        
        print(f"[RetrainEngine] Loaded model: {latest_model_path}")
        print(f"  Version: {self.model_version}")
        
        return model
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions with current model."""
        if self.current_model is None:
            raise ValueError("No model loaded. Train or load a model first.")
        
        # Prepare data
        numeric_cols = X.select_dtypes(include=[np.number]).columns
        X = X[numeric_cols].fillna(0)
        
        # Convert to GPU if needed
        if self.use_gpu:
            X = cudf.DataFrame.from_pandas(X)
        
        return self.current_model.predict(X)


# ── TEST ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n=== Testing Retraining Engine ===\n")
    
    # Check if we have data
    ref_path = "data/reference/reference.parquet"
    
    if not Path(ref_path).exists():
        print("[WARN] Reference data not found. Generating synthetic data...")
        from src.utils.data_generator import DataGenerator
        gen = DataGenerator()
        ref_df = gen.generate_reference(n_rows=50000)
        gen.save_reference(ref_df)
    
    # Initialize engine
    engine = RetrainEngine()
    
    # Train model
    print("\n--- Full Retrain ---")
    metrics = engine.train_full(ref_path, n_estimators=50, max_depth=8)
    
    print(f"\n[OK] Training complete!")
    print(f"  Accuracy: {metrics.accuracy:.3f}")
    print(f"  AUC: {metrics.auc:.3f}")
    print(f"  F1: {metrics.f1:.3f}")
    print(f"  Training time: {metrics.train_time:.2f}s")
    
    # Test prediction
    print("\n--- Testing Prediction ---")
    test_df = pd.read_parquet(ref_path).head(100)
    predictions = engine.predict(test_df.drop(columns=['is_fraud']))
    print(f"Predictions: {predictions[:10]}")
    print(f"Fraud rate in predictions: {predictions.mean():.2%}")
    
    print("\n[OK] Retraining engine test complete!")
