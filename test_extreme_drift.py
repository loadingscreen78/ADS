"""
Quick test to verify extreme drift batch triggers RETRAIN_FULL
"""

import pandas as pd
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.drift.drift_engine import DriftEngine
from src.scheduler.cara import CARAScheduler

def test_extreme_drift():
    print("\n" + "="*80)
    print("  TESTING EXTREME DRIFT BATCH")
    print("="*80)
    
    # Load reference data
    ref_path = "data/reference/reference.parquet"
    if not Path(ref_path).exists():
        print(f"❌ Reference data not found: {ref_path}")
        return
    
    # Load extreme drift batch
    extreme_path = "extreme_drift/extreme_drift_50K.parquet"
    if not Path(extreme_path).exists():
        print(f"❌ Extreme drift batch not found: {extreme_path}")
        return
    
    print(f"\n[1/3] Loading data...")
    ref_df = pd.read_parquet(ref_path)
    extreme_df = pd.read_parquet(extreme_path)
    
    print(f"  ✓ Reference: {len(ref_df):,} rows, {ref_df['is_fraud'].mean():.2%} fraud")
    print(f"  ✓ Extreme: {len(extreme_df):,} rows, {extreme_df['is_fraud'].mean():.2%} fraud")
    
    # Initialize drift engine
    print(f"\n[2/3] Running drift detection...")
    drift_engine = DriftEngine(ref_path)
    drift_score = drift_engine.analyze_batch(extreme_path, "extreme_test")
    
    print(f"  ✓ Drift Ratio: {drift_score.drift_ratio:.1%}")
    print(f"  ✓ Average PSI: {drift_score.avg_psi:.3f}")
    print(f"  ✓ Max PSI: {drift_score.max_psi:.3f}")
    print(f"  ✓ Severity: {drift_score.overall_severity}")
    print(f"  ✓ Features Confirmed Drifted: {len(drift_score.confirmed_drift)}")
    
    # Get CARA decision
    print(f"\n[3/3] Running CARA analysis...")
    cara = CARAScheduler()
    decision = cara.decide(
        drift_score=drift_score,
        current_acc=0.95,
        baseline_acc=0.95,
        data_quality=0.85
    )
    
    print(f"  ✓ CARA Score: {decision.score:.3f}")
    print(f"  ✓ CARA Decision: {decision.decision.value}")
    print(f"  ✓ Expected Gain: {decision.expected_gain:.1%}")
    print(f"  ✓ Justification: {decision.justification}")
    
    # Verify result
    print("\n" + "="*80)
    if decision.decision.value == "FULL_RETRAIN":
        print("  ✅ SUCCESS: FULL_RETRAIN TRIGGERED!")
        print("  This batch will trigger full retraining in the dashboard!")
    else:
        print(f"  ❌ UNEXPECTED: Got {decision.decision.value} instead of FULL_RETRAIN")
        print(f"  Drift ratio: {drift_score.drift_ratio:.1%} (need > 60%)")
        print(f"  Severity: {drift_score.overall_severity} (need SIGNIFICANT)")
        print(f"  CARA score: {decision.score:.3f} (need > 0.7)")
    print("="*80 + "\n")

if __name__ == "__main__":
    test_extreme_drift()
