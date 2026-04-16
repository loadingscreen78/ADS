# tests/test_cara.py
"""Unit tests for CARA Scheduler"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.drift.drift_engine import DriftEngine
from src.scheduler.cara import CARAScheduler, RetrainDecision


def test_cara_no_action():
    """Test CARA on clean data - should return NO_ACTION"""
    print("\n=== Test 1: CARA on Clean Data ===")
    engine = DriftEngine("data/reference/reference.parquet")
    cara = CARAScheduler(gpu_cost_per_hr=0.5, retrain_time_hr=0.1)
    
    score = engine.analyze_batch("data/production/batch_001_clean.parquet", "001")
    decision = cara.decide(score, current_acc=0.94, baseline_acc=0.95)
    
    print(f"Decision: {decision.decision.value}")
    print(f"CARA Score: {decision.score:.4f}")
    
    assert decision.decision == RetrainDecision.NO_ACTION, "Should be NO_ACTION for clean data"
    print("✓ Test passed: NO_ACTION for clean data")


def test_cara_retrain_decision():
    """Test CARA on severe drift - should trigger retrain"""
    print("\n=== Test 2: CARA on Severe Drift ===")
    engine = DriftEngine("data/reference/reference.parquet")
    cara = CARAScheduler(gpu_cost_per_hr=0.5, retrain_time_hr=0.1)
    
    score = engine.analyze_batch("data/production/batch_003_severe.parquet", "003")
    decision = cara.decide(score, current_acc=0.87, baseline_acc=0.95)
    
    print(f"Decision: {decision.decision.value}")
    print(f"CARA Score: {decision.score:.4f}")
    
    # Should trigger some form of retraining
    assert decision.decision in [RetrainDecision.FULL_RETRAIN, RetrainDecision.INCREMENTAL], \
        "Should trigger retrain for severe drift"
    print("✓ Test passed: Retrain triggered for severe drift")


def test_cara_safety_floor():
    """Test CARA safety floor - should force retrain on accuracy drop"""
    print("\n=== Test 3: CARA Safety Floor ===")
    engine = DriftEngine("data/reference/reference.parquet")
    cara = CARAScheduler(gpu_cost_per_hr=0.5, retrain_time_hr=0.1)
    
    score = engine.analyze_batch("data/production/batch_001_clean.parquet", "001")
    decision = cara.decide(score, current_acc=0.82, baseline_acc=0.95)  # 13% drop
    
    print(f"Decision: {decision.decision.value}")
    print(f"Accuracy drop: {0.95 - 0.82:.2%}")
    
    assert decision.decision == RetrainDecision.FULL_RETRAIN, "Safety floor should force retrain"
    print("✓ Test passed: Safety floor triggered correctly")


if __name__ == "__main__":
    test_cara_no_action()
    test_cara_retrain_decision()
    test_cara_safety_floor()
    print("\n✓ All CARA tests passed!")
