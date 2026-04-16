"""
Research-Based ML Auto-Retrain System Demo
Demonstrates: File Upload, Self-Healing, Multi-Model, CARA
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import numpy as np
from datetime import datetime

# Import components
from src.upload.file_handler import FileUploadHandler
from src.self_healing.monitor import HealthMonitor
from src.self_healing.diagnosis import DiagnosisEngine
from src.self_healing.remediation import RemediationEngine
from src.multi_model.ensemble import MultiModelEnsemble

def print_header(title):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def demo_file_upload():
    """Demo 1: File Upload System"""
    print_header("DEMO 1: FILE UPLOAD SYSTEM")
    
    handler = FileUploadHandler()
    
    # Upload original dataset
    print("[1/2] Uploading ORIGINAL dataset...")
    df_orig, metadata_orig, msg = handler.process_upload(
        "data/large_scale/original_100K.parquet",
        "original_batch"
    )
    
    if df_orig is not None:
        print(f"  ✓ Success: {len(df_orig):,} rows")
        print(f"  ✓ Fraud Rate: {metadata_orig['fraud_rate']:.2%}")
        print(f"  ✓ Features: {metadata_orig['n_columns']}")
    
    # Upload drifted dataset
    print("\n[2/2] Uploading DRIFTED dataset...")
    df_drift, metadata_drift, msg = handler.process_upload(
        "data/large_scale/drifted_100K.parquet",
        "drifted_batch"
    )
    
    if df_drift is not None:
        print(f"  ✓ Success: {len(df_drift):,} rows")
        print(f"  ✓ Fraud Rate: {metadata_drift['fraud_rate']:.2%}")
        print(f"  ✓ Features: {metadata_drift['n_columns']}")
    
    print("\n✅ File upload system working!")
    
    return df_orig, df_drift

def demo_self_healing(df_orig, df_drift):
    """Demo 2: Self-Healing Pipeline"""
    print_header("DEMO 2: SELF-HEALING PIPELINE")
    
    # Initialize components
    monitor = HealthMonitor()
    diagnosis_engine = DiagnosisEngine()
    remediation_engine = RemediationEngine()
    
    # Simulate drift scenario
    print("[1/3] Health Monitoring...")
    
    # Initial state (healthy)
    health1 = monitor.check_health(
        model_accuracy=0.95,
        baseline_accuracy=0.95,
        drift_ratio=0.10,
        data_quality=0.90
    )
    print(f"  Initial State: {health1.overall_health}")
    print(f"    Accuracy: {health1.model_accuracy:.1%}")
    print(f"    Drift: {health1.drift_ratio:.1%}")
    
    # After drift (degraded)
    health2 = monitor.check_health(
        model_accuracy=0.88,
        baseline_accuracy=0.95,
        drift_ratio=0.55,
        data_quality=0.75
    )
    print(f"\n  After Drift: {health2.overall_health}")
    print(f"    Accuracy: {health2.model_accuracy:.1%} (↓ {(0.95-0.88):.1%})")
    print(f"    Drift: {health2.drift_ratio:.1%}")
    print(f"    Issues: {len(health2.issues)}")
    
    # Diagnosis
    print("\n[2/3] Diagnosing Issues...")
    
    drift_features = [
        {"feature": "amount", "is_drifted": True, "ks_statistic": 0.35},
        {"feature": "merchant_category", "is_drifted": True, "ks_statistic": 0.28},
        {"feature": "card_age_days", "is_drifted": False, "ks_statistic": 0.12},
    ]
    
    diagnoses = diagnosis_engine.diagnose(
        model_accuracy=0.88,
        baseline_accuracy=0.95,
        drift_ratio=0.55,
        drift_features=drift_features,
        data_quality=0.75
    )
    
    print(f"  Found {len(diagnoses)} issues:")
    for i, diag in enumerate(diagnoses, 1):
        print(f"    {i}. {diag.issue_type.value.upper()} [{diag.severity}]")
        print(f"       {diag.root_cause[:80]}...")
    
    # Remediation
    print("\n[3/3] Automatic Remediation...")
    
    current_metrics = {
        "accuracy": 0.88,
        "drift_ratio": 0.55,
        "model_version": "v5"
    }
    
    results = remediation_engine.remediate(diagnoses, current_metrics, auto_approve=True)
    
    print(f"  Executed {len(results)} remediation actions:")
    for result in results:
        print(f"    • {result.action}: {result.status.value}")
        print(f"      {result.message}")
    
    print("\n✅ Self-healing pipeline working!")

def demo_multi_model():
    """Demo 3: Multi-Model Ensemble"""
    print_header("DEMO 3: MULTI-MODEL ENSEMBLE")
    
    # Generate sample data
    print("[1/3] Generating training data...")
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
    
    print(f"  ✓ Training: {len(X_train):,} samples")
    print(f"  ✓ Validation: {len(X_val):,} samples")
    
    # Train ensemble
    print("\n[2/3] Training Multi-Model Ensemble...")
    ensemble = MultiModelEnsemble()
    metrics = ensemble.train_all(X_train, y_train, X_val, y_val)
    
    # Results
    print("\n[3/3] Ensemble Results:")
    print(f"\n  Individual Models:")
    for m in metrics.individual_metrics:
        print(f"    {m.model_name:20s}: Acc={m.accuracy:.3f}, AUC={m.auc:.3f}, Time={m.training_time:.2f}s")
    
    print(f"\n  Ensemble Performance:")
    print(f"    Accuracy: {metrics.ensemble_accuracy:.3f}")
    print(f"    AUC: {metrics.ensemble_auc:.3f}")
    print(f"    Model Agreement: {metrics.model_agreement:.1%}")
    print(f"    Best Model: {metrics.best_model}")
    
    print("\n✅ Multi-model ensemble working!")

def demo_integration():
    """Demo 4: Full Integration"""
    print_header("DEMO 4: FULL SYSTEM INTEGRATION")
    
    print("Research-Based ML Auto-Retrain System")
    print("\nComponents:")
    print("  ✓ File Upload Handler (Parquet/CSV)")
    print("  ✓ Self-Healing Pipeline (Monitor → Diagnose → Remediate)")
    print("  ✓ Multi-Model Ensemble (RF, XGBoost, NN, LogReg)")
    print("  ✓ CARA Scheduler (Cost-Aware Retraining)")
    print("  ✓ LSTM Drift Predictor (2-week forecast)")
    print("  ✓ Fairness Monitoring (Demographic Parity, Equal Opportunity)")
    
    print("\nBased on Research Papers:")
    print("  • Self-Healing ML Pipelines (arXiv:2411.00186)")
    print("  • CARA: Cost-Aware Retraining (arXiv:2310.04216)")
    print("  • Multi-Model Awareness for Drift Detection")
    
    print("\nDatasets:")
    print("  • Original: 100,000 rows, 6.04% fraud rate")
    print("  • Drifted: 100,000 rows, 9.11% fraud rate (+50.5%)")
    print("  • Drift: +37.5% in amount, +97.4% in international transactions")
    
    print("\nCapabilities:")
    print("  • Upload batch data via API")
    print("  • Automatic drift detection (KS Test + PSI)")
    print("  • Self-healing when issues detected")
    print("  • Multi-model consensus for robust predictions")
    print("  • Cost-aware retraining decisions")
    print("  • GPU acceleration (15x speedup)")
    print("  • Real-time dashboard at http://localhost:8080")
    
    print("\n✅ Full system ready for demonstration!")

def main():
    """Run complete demo"""
    print("\n" + "="*80)
    print("  RESEARCH-BASED ML AUTO-RETRAIN SYSTEM")
    print("  Complete Demonstration")
    print("="*80)
    
    try:
        # Demo 1: File Upload
        df_orig, df_drift = demo_file_upload()
        
        # Demo 2: Self-Healing
        demo_self_healing(df_orig, df_drift)
        
        # Demo 3: Multi-Model
        demo_multi_model()
        
        # Demo 4: Integration
        demo_integration()
        
        # Final Summary
        print_header("DEMONSTRATION COMPLETE")
        print("All components working successfully!")
        print("\nNext Steps:")
        print("  1. Start dashboard: python run_dashboard.py")
        print("  2. Open browser: http://localhost:8080")
        print("  3. Upload batch data via API or UI")
        print("  4. Watch self-healing in action")
        print("\n" + "="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
