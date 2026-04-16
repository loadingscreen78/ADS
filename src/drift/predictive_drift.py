"""
Predictive Drift Detection using LSTM
Forecasts future drift scores based on historical drift patterns.

This is the key innovation: instead of just detecting drift AFTER it happens,
we predict WHEN drift will occur so we can retrain proactively.
"""

import numpy as np
import pandas as pd
from typing import List, Tuple, Optional
import pickle
from pathlib import Path
import time

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("[WARN] TensorFlow not available. Install with: pip install tensorflow")


class DriftHistory:
    """Stores historical drift scores for LSTM training."""
    
    def __init__(self):
        self.timestamps = []
        self.drift_ratios = []
        self.avg_psi_scores = []
        self.max_psi_scores = []
        self.severities = []
        
    def add_score(self, timestamp: str, drift_ratio: float, 
                  avg_psi: float, max_psi: float, severity: str):
        """Add a drift score to history."""
        self.timestamps.append(timestamp)
        self.drift_ratios.append(drift_ratio)
        self.avg_psi_scores.append(avg_psi)
        self.max_psi_scores.append(max_psi)
        self.severities.append(severity)
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert to DataFrame for analysis."""
        return pd.DataFrame({
            'timestamp': self.timestamps,
            'drift_ratio': self.drift_ratios,
            'avg_psi': self.avg_psi_scores,
            'max_psi': self.max_psi_scores,
            'severity': self.severities
        })
    
    def save(self, filepath: str):
        """Save history to disk."""
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)
        print(f"[DriftHistory] Saved to {filepath}")
    
    @staticmethod
    def load(filepath: str) -> 'DriftHistory':
        """Load history from disk."""
        with open(filepath, 'rb') as f:
            return pickle.load(f)


class LSTMDriftPredictor:
    """
    LSTM-based drift predictor.
    
    Trains on historical drift scores to forecast future drift.
    Uses a sequence of past drift measurements to predict next N weeks.
    
    Architecture:
        - Input: sequence of drift scores (lookback window)
        - LSTM layers: capture temporal patterns
        - Output: predicted drift scores for next N steps
    """
    
    def __init__(self, lookback: int = 4, forecast_horizon: int = 2):
        """
        Args:
            lookback: Number of past weeks to use for prediction
            forecast_horizon: Number of weeks to forecast ahead
        """
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow required for LSTM predictor")
        
        self.lookback = lookback
        self.forecast_horizon = forecast_horizon
        self.model = None
        self.scaler_mean = None
        self.scaler_std = None
        
    def _prepare_sequences(self, drift_scores: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sequences for LSTM training.
        
        Input: [week1, week2, week3, week4, week5, week6, ...]
        Output: 
            X: [[week1, week2, week3, week4], [week2, week3, week4, week5], ...]
            y: [[week5, week6], [week6, week7], ...]
        """
        X, y = [], []
        
        for i in range(len(drift_scores) - self.lookback - self.forecast_horizon + 1):
            X.append(drift_scores[i:i + self.lookback])
            y.append(drift_scores[i + self.lookback:i + self.lookback + self.forecast_horizon])
        
        return np.array(X), np.array(y)
    
    def _normalize(self, data: np.ndarray, fit: bool = False) -> np.ndarray:
        """Normalize data using z-score normalization."""
        if fit:
            self.scaler_mean = np.mean(data)
            self.scaler_std = np.std(data) + 1e-8
        
        return (data - self.scaler_mean) / self.scaler_std
    
    def _denormalize(self, data: np.ndarray) -> np.ndarray:
        """Denormalize predictions."""
        return data * self.scaler_std + self.scaler_mean
    
    def build_model(self, input_shape: Tuple[int, int]):
        """
        Build LSTM model architecture.
        
        Args:
            input_shape: (lookback, n_features)
        """
        model = keras.Sequential([
            layers.LSTM(64, activation='relu', return_sequences=True, 
                       input_shape=input_shape),
            layers.Dropout(0.2),
            layers.LSTM(32, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(16, activation='relu'),
            layers.Dense(self.forecast_horizon)
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        self.model = model
        print(f"[LSTM] Model built: {model.count_params():,} parameters")
        return model
    
    def train(self, drift_history: DriftHistory, epochs: int = 100, 
              validation_split: float = 0.2) -> dict:
        """
        Train LSTM on historical drift scores.
        
        Args:
            drift_history: Historical drift measurements
            epochs: Training epochs
            validation_split: Fraction of data for validation
            
        Returns:
            Training history
        """
        print(f"[LSTM] Training predictor...")
        print(f"  Lookback: {self.lookback} weeks")
        print(f"  Forecast: {self.forecast_horizon} weeks ahead")
        
        # Extract drift ratios as target variable
        drift_scores = np.array(drift_history.drift_ratios)
        
        if len(drift_scores) < self.lookback + self.forecast_horizon:
            raise ValueError(f"Need at least {self.lookback + self.forecast_horizon} "
                           f"historical measurements, got {len(drift_scores)}")
        
        # Normalize
        drift_scores_norm = self._normalize(drift_scores, fit=True)
        
        # Create sequences
        X, y = self._prepare_sequences(drift_scores_norm)
        
        # Reshape for LSTM: (samples, timesteps, features)
        X = X.reshape(X.shape[0], X.shape[1], 1)
        
        print(f"[LSTM] Training data: {X.shape[0]} sequences")
        print(f"  X shape: {X.shape}")
        print(f"  y shape: {y.shape}")
        
        # Build model if not exists
        if self.model is None:
            self.build_model(input_shape=(self.lookback, 1))
        
        # Train
        t_start = time.time()
        history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=8,
            validation_split=validation_split,
            verbose=0,
            callbacks=[
                keras.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=15,
                    restore_best_weights=True
                )
            ]
        )
        
        elapsed = time.time() - t_start
        final_loss = history.history['loss'][-1]
        final_val_loss = history.history['val_loss'][-1]
        
        print(f"[LSTM] Training complete in {elapsed:.1f}s")
        print(f"  Final loss: {final_loss:.4f}")
        print(f"  Final val_loss: {final_val_loss:.4f}")
        
        return history.history
    
    def predict(self, recent_drift_scores: List[float]) -> np.ndarray:
        """
        Predict future drift scores.
        
        Args:
            recent_drift_scores: List of recent drift ratios (length = lookback)
            
        Returns:
            Predicted drift scores for next forecast_horizon weeks
        """
        if len(recent_drift_scores) < self.lookback:
            raise ValueError(f"Need {self.lookback} recent scores, got {len(recent_drift_scores)}")
        
        # Take last lookback scores
        input_seq = np.array(recent_drift_scores[-self.lookback:])
        
        # Normalize
        input_seq_norm = self._normalize(input_seq, fit=False)
        
        # Reshape for LSTM
        X = input_seq_norm.reshape(1, self.lookback, 1)
        
        # Predict
        pred_norm = self.model.predict(X, verbose=0)[0]
        
        # Denormalize
        pred = self._denormalize(pred_norm)
        
        # Clip to valid range [0, 1]
        pred = np.clip(pred, 0, 1)
        
        return pred
    
    def save(self, filepath: str):
        """Save model to disk."""
        model_path = Path(filepath)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.model.save(str(model_path))
        
        # Save scaler parameters
        scaler_path = model_path.parent / f"{model_path.stem}_scaler.pkl"
        with open(scaler_path, 'wb') as f:
            pickle.dump({
                'mean': self.scaler_mean,
                'std': self.scaler_std,
                'lookback': self.lookback,
                'forecast_horizon': self.forecast_horizon
            }, f)
        
        print(f"[LSTM] Model saved to {filepath}")
    
    @staticmethod
    def load(filepath: str) -> 'LSTMDriftPredictor':
        """Load model from disk."""
        model = keras.models.load_model(filepath)
        
        # Load scaler
        model_path = Path(filepath)
        scaler_path = model_path.parent / f"{model_path.stem}_scaler.pkl"
        with open(scaler_path, 'rb') as f:
            scaler_data = pickle.load(f)
        
        predictor = LSTMDriftPredictor(
            lookback=scaler_data['lookback'],
            forecast_horizon=scaler_data['forecast_horizon']
        )
        predictor.model = model
        predictor.scaler_mean = scaler_data['mean']
        predictor.scaler_std = scaler_data['std']
        
        print(f"[LSTM] Model loaded from {filepath}")
        return predictor


# ── TEST ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not TF_AVAILABLE:
        print("[ERROR] TensorFlow not installed. Run: pip install tensorflow")
        exit(1)
    
    print("\n=== Testing LSTM Drift Predictor ===\n")
    
    # Simulate 20 weeks of drift scores
    np.random.seed(42)
    
    # Create realistic drift pattern: gradual increase with noise
    weeks = 20
    base_drift = np.linspace(0.1, 0.6, weeks)  # Gradual increase
    noise = np.random.normal(0, 0.05, weeks)
    drift_scores = np.clip(base_drift + noise, 0, 1)
    
    # Create drift history
    history = DriftHistory()
    for i, score in enumerate(drift_scores):
        history.add_score(
            timestamp=f"2024-W{i+1:02d}",
            drift_ratio=score,
            avg_psi=score * 0.3,
            max_psi=score * 0.5,
            severity="MODERATE" if score > 0.25 else "LOW"
        )
    
    print("Historical drift scores:")
    print(history.to_dataframe())
    
    # Train predictor
    predictor = LSTMDriftPredictor(lookback=4, forecast_horizon=2)
    train_history = predictor.train(history, epochs=50)
    
    # Make prediction
    recent_scores = drift_scores[-4:]
    print(f"\nRecent 4 weeks: {recent_scores}")
    
    prediction = predictor.predict(recent_scores.tolist())
    print(f"Predicted next 2 weeks: {prediction}")
    
    # Compare with actual (if we had it)
    print(f"\nPrediction interpretation:")
    for i, pred_score in enumerate(prediction):
        week_num = len(drift_scores) + i + 1
        if pred_score > 0.5:
            severity = "CRITICAL"
        elif pred_score > 0.25:
            severity = "SIGNIFICANT"
        else:
            severity = "LOW"
        print(f"  Week {week_num}: drift_ratio={pred_score:.3f} → {severity}")
    
    # Save model
    predictor.save("data/models/lstm_drift_predictor.h5")
    history.save("data/models/drift_history.pkl")
    
    print("\n[OK] LSTM predictor test complete!")
