"""
Implementation Verification Script
Quickly checks that all Day 1-6 components are working correctly
"""

import sys
from pathlib import Path

print("=" * 70)
print("DAY 1-6 IMPLEMENTATION VERIFICATION")
print("=" * 70)
print()

errors = []
warnings = []
successes = []

# ═══════════════════════════════════════════════════════════════════════
# Check 1: File Structure
# ═══════════════════════════════════════════════════════════════════════
print("Check 1: File Structure")
print("-" * 70)

required_files = [
    "check_env.py",
    "run_day1_to_day6.py",
    "requirements.txt",
    "README.md",
    "DAY1_TO_DAY6_IMPLEMENTATION.md",
    "src/utils/data_generator.py",
    "src/drift/ks_detector.py",
    "src/drift/psi_detector.py",
    "src/drift/drift_engine.py",
    "src/drift/predictive_drift.py",
    "src/scheduler/cara.py",
    "src/retraining/retrain_engine.py",
    "tests/test_ks.py",
    "tests/test_psi.py",
    "tests/test_cara.py"
]

for filepath in required_files:
    if Path(filepath).exists():
        print(f"  ✓ {filepath}")
        successes.append(f"File exists: {filepath}")
    else:
        print(f"  ✗ {filepath} - MISSING")
        errors.append(f"Missing file: {filepath}")

# ═══════════════════════════════════════════════════════════════════════
# Check 2: Dependencies
# ═══════════════════════════════════════════════════════════════════════
print("\nCheck 2: Dependencies")
print("-" * 70)

dependencies = [
    ("numpy", "numpy"),
    ("pandas", "pandas"),
    ("scipy", "scipy"),
    ("sklearn", "scikit-learn"),
    ("mlflow", "mlflow"),
    ("tensorflow", "tensorflow"),
    ("joblib", "joblib"),
    ("pyarrow", "pyarrow")
]

for module_name, package_name in dependencies:
    try:
        __import__(module_name)
        print(f"  ✓ {package_name}")
        successes.append(f"Dependency installed: {package_name}")
    except ImportError:
        print(f"  ✗ {package_name} - NOT INSTALLED")
        errors.append(f"Missing dependency: {package_name}")

# Check optional GPU dependencies
print("\n  Optional GPU Dependencies:")
try:
    import cudf
    import cuml
    print(f"  ✓ RAPIDS (cuDF, cuML) - GPU mode available")
    successes.append("GPU acceleration available")
except ImportError:
    print(f"  ⚠ RAPIDS not installed - CPU mode only")
    warnings.append("GPU acceleration not available (optional)")

# ═══════════════════════════════════════════════════════════════════════
# Check 3: Import Tests
# ═══════════════════════════════════════════════════════════════════════
print("\nCheck 3: Module Imports")
print("-" * 70)

modules_to_test = [
    ("src.utils.data_generator", "DataGenerator"),
    ("src.drift.ks_detector", "KSDriftDetector"),
    ("src.drift.psi_detector", "PSIDriftDetector"),
    ("src.drift.drift_engine", "DriftEngine"),
    ("src.drift.predictive_drift", "LSTMDriftPredictor"),
    ("src.scheduler.cara", "CARAScheduler"),
    ("src.retraining.retrain_engine", "RetrainEngine")
]

for module_path, class_name in modules_to_test:
    try:
        module = __import__(module_path, fromlist=[class_name])
        cls = getattr(module, class_name)
        print(f"  ✓ {module_path}.{class_name}")
        successes.append(f"Module imports: {module_path}")
    except Exception as e:
        print(f"  ✗ {module_path}.{class_name} - ERROR: {e}")
        errors.append(f"Import error: {module_path} - {e}")

# ═══════════════════════════════════════════════════════════════════════
# Check 4: Data Generation Test
# ═══════════════════════════════════════════════════════════════════════
print("\nCheck 4: Data Generation")
print("-" * 70)

try:
    from src.utils.data_generator import DataGenerator
    
    gen = DataGenerator()
    test_df = gen.generate_reference(n_rows=1000)
    
    if len(test_df) == 1000:
        print(f"  ✓ Generated test data: {len(test_df)} rows")
        successes.append("Data generation works")
    else:
        print(f"  ✗ Wrong number of rows: {len(test_df)}")
        errors.append("Data generation produced wrong size")
    
    if 'is_fraud' in test_df.columns:
        print(f"  ✓ Fraud label present")
        successes.append("Fraud label exists")
    else:
        print(f"  ✗ Fraud label missing")
        errors.append("Fraud label missing from generated data")
    
    fraud_rate = test_df['is_fraud'].mean()
    if 0.01 < fraud_rate < 0.10:
        print(f"  ✓ Fraud rate: {fraud_rate:.2%} (realistic)")
        successes.append(f"Fraud rate realistic: {fraud_rate:.2%}")
    else:
        print(f"  ⚠ Fraud rate: {fraud_rate:.2%} (unusual)")
        warnings.append(f"Fraud rate unusual: {fraud_rate:.2%}")

except Exception as e:
    print(f"  ✗ Data generation failed: {e}")
    errors.append(f"Data generation error: {e}")

# ═══════════════════════════════════════════════════════════════════════
# Check 5: Drift Detection Test
# ═══════════════════════════════════════════════════════════════════════
print("\nCheck 5: Drift Detection")
print("-" * 70)

try:
    from src.drift.ks_detector import KSDriftDetector
    from src.drift.psi_detector import PSIDriftDetector
    import tempfile
    import os
    
    # Create temp data
    gen = DataGenerator()
    ref_df = gen.generate_reference(n_rows=5000)
    prod_df = gen.generate_drifted(n_rows=2000, drift_level="severe")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        ref_path = os.path.join(tmpdir, "ref.parquet")
        prod_path = os.path.join(tmpdir, "prod.parquet")
        
        ref_df.to_parquet(ref_path, index=False)
        prod_df.to_parquet(prod_path, index=False)
        
        # Test KS detector
        ks = KSDriftDetector(ref_path)
        ks_results = ks.detect(prod_path)
        
        if len(ks_results) > 0:
            print(f"  ✓ KS detector works: {len(ks_results)} features analyzed")
            successes.append("KS detector functional")
        else:
            print(f"  ✗ KS detector returned no results")
            errors.append("KS detector failed")
        
        # Test PSI detector
        psi = PSIDriftDetector(ref_path)
        psi_results = psi.detect(prod_path)
        
        if len(psi_results) > 0:
            print(f"  ✓ PSI detector works: {len(psi_results)} features analyzed")
            successes.append("PSI detector functional")
        else:
            print(f"  ✗ PSI detector returned no results")
            errors.append("PSI detector failed")

except Exception as e:
    print(f"  ✗ Drift detection test failed: {e}")
    errors.append(f"Drift detection error: {e}")

# ═══════════════════════════════════════════════════════════════════════
# Check 6: CARA Scheduler Test
# ═══════════════════════════════════════════════════════════════════════
print("\nCheck 6: CARA Scheduler")
print("-" * 70)

try:
    from src.scheduler.cara import CARAScheduler
    from src.drift.drift_engine import DriftScore
    
    # Create mock drift score
    mock_score = type('DriftScore', (), {
        'batch_id': 'test',
        'drift_ratio': 0.5,
        'avg_psi': 0.3,
        'max_psi': 0.4,
        'overall_severity': 'SIGNIFICANT',
        'confirmed_drift': ['amount', 'is_international']
    })()
    
    cara = CARAScheduler()
    decision = cara.decide(mock_score, current_acc=0.90, baseline_acc=0.95)
    
    if decision.decision:
        print(f"  ✓ CARA decision: {decision.decision.value}")
        print(f"  ✓ CARA score: {decision.score:.3f}")
        successes.append("CARA scheduler functional")
    else:
        print(f"  ✗ CARA returned no decision")
        errors.append("CARA scheduler failed")

except Exception as e:
    print(f"  ✗ CARA test failed: {e}")
    errors.append(f"CARA scheduler error: {e}")

# ═══════════════════════════════════════════════════════════════════════
# Check 7: LSTM Predictor Test
# ═══════════════════════════════════════════════════════════════════════
print("\nCheck 7: LSTM Drift Predictor")
print("-" * 70)

try:
    import tensorflow as tf
    from src.drift.predictive_drift import LSTMDriftPredictor, DriftHistory
    import numpy as np
    
    # Create mock history
    history = DriftHistory()
    for i in range(20):
        history.add_score(
            timestamp=f"2024-W{i:02d}",
            drift_ratio=0.1 + i * 0.02,
            avg_psi=0.05 + i * 0.01,
            max_psi=0.1 + i * 0.015,
            severity="LOW"
        )
    
    # Train predictor
    predictor = LSTMDriftPredictor(lookback=4, forecast_horizon=2)
    predictor.train(history, epochs=10, validation_split=0.2)
    
    # Make prediction
    recent = history.drift_ratios[-4:]
    prediction = predictor.predict(recent)
    
    if len(prediction) == 2:
        print(f"  ✓ LSTM trained successfully")
        print(f"  ✓ Prediction: {prediction}")
        successes.append("LSTM predictor functional")
    else:
        print(f"  ✗ LSTM prediction wrong size")
        errors.append("LSTM prediction failed")

except ImportError:
    print(f"  ⚠ TensorFlow not installed - LSTM test skipped")
    warnings.append("TensorFlow not available (required for LSTM)")
except Exception as e:
    print(f"  ✗ LSTM test failed: {e}")
    errors.append(f"LSTM predictor error: {e}")

# ═══════════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("VERIFICATION SUMMARY")
print("=" * 70)

print(f"\n✓ Successes: {len(successes)}")
print(f"⚠ Warnings: {len(warnings)}")
print(f"✗ Errors: {len(errors)}")

if errors:
    print("\n" + "=" * 70)
    print("ERRORS FOUND")
    print("=" * 70)
    for error in errors:
        print(f"  ✗ {error}")
    print("\nPlease fix these errors before running the main workflow.")
    sys.exit(1)

if warnings:
    print("\n" + "=" * 70)
    print("WARNINGS")
    print("=" * 70)
    for warning in warnings:
        print(f"  ⚠ {warning}")
    print("\nThese are optional features. System will work without them.")

print("\n" + "=" * 70)
print("✓ ALL CRITICAL CHECKS PASSED")
print("=" * 70)
print("""
The implementation is ready for demonstration!

Next steps:
1. Run complete workflow:
   python run_day1_to_day6.py

2. Review documentation:
   - DAY1_TO_DAY6_IMPLEMENTATION.md (detailed report)
   - QUICKSTART_DAY1_TO_DAY6.md (quick reference)
   - TEACHER_REVIEW_CHECKLIST.md (grading guide)

3. Optional: Setup IEEE dataset:
   python setup_ieee_dataset.py
""")
