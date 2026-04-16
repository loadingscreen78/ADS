"""
Multi-Model Ensemble
Combines multiple model types for robust predictions and drift detection
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import pickle

@dataclass
class ModelMetrics:
    """Metrics for a single model"""
    model_name: str
    accuracy: float
    auc: float
    precision: float
    recall: float
    f1: float
    training_time: float

@dataclass
class EnsembleMetrics:
    """Metrics for ensemble"""
    ensemble_accuracy: float
    ensemble_auc: float
    model_agreement: float  # How much models agree
    best_model: str
    individual_metrics: List[ModelMetrics]

class MultiModelEnsemble:
    """
    Multi-model ensemble for fraud detection
    
    Models:
    - Random Forest (baseline)
    - XGBoost (gradient boosting)
    - Neural Network (deep learning)
    - Logistic Regression (linear baseline)
    """
    
    def __init__(self):
        self.models = {}
        self.model_names = ['random_forest', 'xgboost', 'neural_network', 'logistic_regression']
        self.weights = None  # Learned weights for ensemble
        self.metrics_history = []
        
        print("[MultiModelEnsemble] Initialized")
        print(f"  Models: {', '.join(self.model_names)}")
    
    def train_all(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series
    ) -> EnsembleMetrics:
        """
        Train all models in ensemble
        
        Returns:
            EnsembleMetrics with performance of all models
        """
        print("\n[Ensemble] Training all models...")
        
        individual_metrics = []
        
        # 1. Random Forest
        print("\n  [1/4] Training Random Forest...")
        rf_metrics = self._train_random_forest(X_train, y_train, X_val, y_val)
        individual_metrics.append(rf_metrics)
        print(f"    ✓ Accuracy: {rf_metrics.accuracy:.3f}, AUC: {rf_metrics.auc:.3f}")
        
        # 2. XGBoost
        print("\n  [2/4] Training XGBoost...")
        xgb_metrics = self._train_xgboost(X_train, y_train, X_val, y_val)
        individual_metrics.append(xgb_metrics)
        print(f"    ✓ Accuracy: {xgb_metrics.accuracy:.3f}, AUC: {xgb_metrics.auc:.3f}")
        
        # 3. Neural Network
        print("\n  [3/4] Training Neural Network...")
        nn_metrics = self._train_neural_network(X_train, y_train, X_val, y_val)
        individual_metrics.append(nn_metrics)
        print(f"    ✓ Accuracy: {nn_metrics.accuracy:.3f}, AUC: {nn_metrics.auc:.3f}")
        
        # 4. Logistic Regression
        print("\n  [4/4] Training Logistic Regression...")
        lr_metrics = self._train_logistic_regression(X_train, y_train, X_val, y_val)
        individual_metrics.append(lr_metrics)
        print(f"    ✓ Accuracy: {lr_metrics.accuracy:.3f}, AUC: {lr_metrics.auc:.3f}")
        
        # Calculate ensemble metrics
        print("\n  [5/5] Calculating ensemble performance...")
        ensemble_metrics = self._calculate_ensemble_metrics(X_val, y_val, individual_metrics)
        
        self.metrics_history.append(ensemble_metrics)
        
        print(f"\n✓ Ensemble trained successfully!")
        print(f"  Ensemble Accuracy: {ensemble_metrics.ensemble_accuracy:.3f}")
        print(f"  Model Agreement: {ensemble_metrics.model_agreement:.1%}")
        print(f"  Best Model: {ensemble_metrics.best_model}")
        
        return ensemble_metrics
    
    def _train_random_forest(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series
    ) -> ModelMetrics:
        """Train Random Forest model"""
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.metrics import accuracy_score, roc_auc_score, precision_score, recall_score, f1_score
        import time
        
        start_time = time.time()
        
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            max_features=0.3,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train, y_train)
        
        training_time = time.time() - start_time
        
        # Predictions
        y_pred = model.predict(X_val)
        y_proba = model.predict_proba(X_val)[:, 1]
        
        # Metrics
        self.models['random_forest'] = model
        
        return ModelMetrics(
            model_name='random_forest',
            accuracy=accuracy_score(y_val, y_pred),
            auc=roc_auc_score(y_val, y_proba),
            precision=precision_score(y_val, y_pred),
            recall=recall_score(y_val, y_pred),
            f1=f1_score(y_val, y_pred),
            training_time=training_time
        )
    
    def _train_xgboost(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series
    ) -> ModelMetrics:
        """Train XGBoost model"""
        try:
            import xgboost as xgb
            from sklearn.metrics import accuracy_score, roc_auc_score, precision_score, recall_score, f1_score
            import time
            
            start_time = time.time()
            
            model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                n_jobs=-1,
                eval_metric='logloss'
            )
            model.fit(X_train, y_train, verbose=False)
            
            training_time = time.time() - start_time
            
            # Predictions
            y_pred = model.predict(X_val)
            y_proba = model.predict_proba(X_val)[:, 1]
            
            # Metrics
            self.models['xgboost'] = model
            
            return ModelMetrics(
                model_name='xgboost',
                accuracy=accuracy_score(y_val, y_pred),
                auc=roc_auc_score(y_val, y_proba),
                precision=precision_score(y_val, y_pred),
                recall=recall_score(y_val, y_pred),
                f1=f1_score(y_val, y_pred),
                training_time=training_time
            )
        except ImportError:
            print("    ⚠ XGBoost not installed, using Random Forest as fallback")
            return self._train_random_forest(X_train, y_train, X_val, y_val)
    
    def _train_neural_network(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series
    ) -> ModelMetrics:
        """Train Neural Network model"""
        from sklearn.neural_network import MLPClassifier
        from sklearn.metrics import accuracy_score, roc_auc_score, precision_score, recall_score, f1_score
        import time
        
        start_time = time.time()
        
        model = MLPClassifier(
            hidden_layer_sizes=(64, 32, 16),
            activation='relu',
            solver='adam',
            max_iter=100,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.1
        )
        model.fit(X_train, y_train)
        
        training_time = time.time() - start_time
        
        # Predictions
        y_pred = model.predict(X_val)
        y_proba = model.predict_proba(X_val)[:, 1]
        
        # Metrics
        self.models['neural_network'] = model
        
        return ModelMetrics(
            model_name='neural_network',
            accuracy=accuracy_score(y_val, y_pred),
            auc=roc_auc_score(y_val, y_proba),
            precision=precision_score(y_val, y_pred),
            recall=recall_score(y_val, y_pred),
            f1=f1_score(y_val, y_pred),
            training_time=training_time
        )
    
    def _train_logistic_regression(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series
    ) -> ModelMetrics:
        """Train Logistic Regression model"""
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import accuracy_score, roc_auc_score, precision_score, recall_score, f1_score
        import time
        
        start_time = time.time()
        
        model = LogisticRegression(
            max_iter=1000,
            random_state=42,
            n_jobs=1  # Use single job to avoid memory issues
        )
        model.fit(X_train, y_train)
        
        training_time = time.time() - start_time
        
        # Predictions
        y_pred = model.predict(X_val)
        y_proba = model.predict_proba(X_val)[:, 1]
        
        # Metrics
        self.models['logistic_regression'] = model
        
        return ModelMetrics(
            model_name='logistic_regression',
            accuracy=accuracy_score(y_val, y_pred),
            auc=roc_auc_score(y_val, y_proba),
            precision=precision_score(y_val, y_pred),
            recall=recall_score(y_val, y_pred),
            f1=f1_score(y_val, y_pred),
            training_time=training_time
        )
    
    def _calculate_ensemble_metrics(
        self,
        X_val: pd.DataFrame,
        y_val: pd.Series,
        individual_metrics: List[ModelMetrics]
    ) -> EnsembleMetrics:
        """Calculate ensemble performance"""
        from sklearn.metrics import accuracy_score, roc_auc_score
        
        # Get predictions from all models
        predictions = []
        probabilities = []
        
        for model_name in self.models.keys():
            model = self.models[model_name]
            pred = model.predict(X_val)
            proba = model.predict_proba(X_val)[:, 1]
            predictions.append(pred)
            probabilities.append(proba)
        
        # Ensemble prediction (majority vote)
        predictions = np.array(predictions)
        ensemble_pred = (np.mean(predictions, axis=0) > 0.5).astype(int)
        
        # Ensemble probability (average)
        probabilities = np.array(probabilities)
        ensemble_proba = np.mean(probabilities, axis=0)
        
        # Calculate agreement
        model_agreement = np.mean([
            np.mean(predictions[i] == predictions[j])
            for i in range(len(predictions))
            for j in range(i+1, len(predictions))
        ])
        
        # Find best model
        best_model = max(individual_metrics, key=lambda m: m.accuracy).model_name
        
        return EnsembleMetrics(
            ensemble_accuracy=accuracy_score(y_val, ensemble_pred),
            ensemble_auc=roc_auc_score(y_val, ensemble_proba),
            model_agreement=model_agreement,
            best_model=best_model,
            individual_metrics=individual_metrics
        )
    
    def predict(self, X: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Ensemble prediction
        
        Returns:
            (predictions, probabilities)
        """
        if not self.models:
            raise ValueError("No models trained yet")
        
        predictions = []
        probabilities = []
        
        for model_name in self.models.keys():
            model = self.models[model_name]
            pred = model.predict(X)
            proba = model.predict_proba(X)[:, 1]
            predictions.append(pred)
            probabilities.append(proba)
        
        # Ensemble
        predictions = np.array(predictions)
        probabilities = np.array(probabilities)
        
        ensemble_pred = (np.mean(predictions, axis=0) > 0.5).astype(int)
        ensemble_proba = np.mean(probabilities, axis=0)
        
        return ensemble_pred, ensemble_proba
    
    def save(self, save_dir: str = "data/models/ensemble"):
        """Save all models"""
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        
        for model_name, model in self.models.items():
            model_path = save_path / f"{model_name}.pkl"
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
        
        print(f"[Ensemble] Saved {len(self.models)} models to {save_dir}")
    
    def load(self, save_dir: str = "data/models/ensemble"):
        """Load all models"""
        save_path = Path(save_dir)
        
        for model_name in self.model_names:
            model_path = save_path / f"{model_name}.pkl"
            if model_path.exists():
                with open(model_path, 'rb') as f:
                    self.models[model_name] = pickle.load(f)
        
        print(f"[Ensemble] Loaded {len(self.models)} models from {save_dir}")


# Test
if __name__ == "__main__":
    print("\n=== Multi-Model Ensemble Test ===\n")
    
    # Generate sample data
    from sklearn.datasets import make_classification
    from sklearn.model_selection import train_test_split
    
    X, y = make_classification(
        n_samples=10000,
        n_features=10,
        n_informative=8,
        n_redundant=2,
        n_classes=2,
        weights=[0.95, 0.05],
        random_state=42
    )
    
    X = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(10)])
    y = pd.Series(y, name='is_fraud')
    
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train ensemble
    ensemble = MultiModelEnsemble()
    metrics = ensemble.train_all(X_train, y_train, X_val, y_val)
    
    print("\n=== Individual Model Performance ===")
    for m in metrics.individual_metrics:
        print(f"{m.model_name:20s}: Acc={m.accuracy:.3f}, AUC={m.auc:.3f}, F1={m.f1:.3f}, Time={m.training_time:.2f}s")
    
    print(f"\n=== Ensemble Performance ===")
    print(f"Ensemble Accuracy: {metrics.ensemble_accuracy:.3f}")
    print(f"Ensemble AUC: {metrics.ensemble_auc:.3f}")
    print(f"Model Agreement: {metrics.model_agreement:.1%}")
    print(f"Best Model: {metrics.best_model}")
    
    # Test prediction
    print(f"\n=== Test Prediction ===")
    pred, proba = ensemble.predict(X_val.head(5))
    print(f"Predictions: {pred}")
    print(f"Probabilities: {proba}")
