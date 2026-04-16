# tests/test_ks.py
"""Unit tests for KS Drift Detector"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.drift.ks_detector import KSDriftDetector


def test_ks_clean_data():
    """Test KS detector on clean data - should detect no drift"""
    print("\n=== Test 1: KS on Clean Data ===")
    detector = KSDriftDetector("data/reference/reference.parquet")
    results = detector.detect("data/production/batch_001_clean.parquet")
    
    drifted_count = sum(1 for r in results.values() if r.drifted)
    print(f"Drifted features: {drifted_count}/{len(results)}")
    
    # Clean data should have minimal drift
    assert drifted_count < len(results) * 0.3, "Too many features drifted on clean data"
    print("✓ Test passed: Clean data shows minimal drift")


def test_ks_severe_drift():
    """Test KS detector on severe drift - should detect significant drift"""
    print("\n=== Test 2: KS on Severe Drift ===")
    detector = KSDriftDetector("data/reference/reference.parquet")
    results = detector.detect("data/production/batch_003_severe.parquet")
    
    drifted_count = sum(1 for r in results.values() if r.drifted)
    print(f"Drifted features: {drifted_count}/{len(results)}")
    
    # Severe drift should be detected
    assert drifted_count > len(results) * 0.5, "Not enough drift detected on severe data"
    print("✓ Test passed: Severe drift detected correctly")


if __name__ == "__main__":
    test_ks_clean_data()
    test_ks_severe_drift()
    print("\n✓ All KS tests passed!")
