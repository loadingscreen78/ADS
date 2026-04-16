# tests/test_psi.py
"""Unit tests for PSI Drift Detector"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.drift.psi_detector import PSIDriftDetector


def test_psi_clean_data():
    """Test PSI detector on clean data"""
    print("\n=== Test 1: PSI on Clean Data ===")
    detector = PSIDriftDetector("data/reference/reference.parquet")
    results = detector.detect("data/production/batch_001_clean.parquet")
    
    avg_psi = sum(r.psi for r in results.values()) / len(results)
    print(f"Average PSI: {avg_psi:.4f}")
    
    # Clean data should have low PSI
    assert avg_psi < 0.15, f"PSI too high for clean data: {avg_psi}"
    print("✓ Test passed: Clean data has low PSI")


def test_psi_severe_drift():
    """Test PSI detector on severe drift"""
    print("\n=== Test 2: PSI on Severe Drift ===")
    detector = PSIDriftDetector("data/reference/reference.parquet")
    results = detector.detect("data/production/batch_003_severe.parquet")
    
    max_psi = max(r.psi for r in results.values())
    print(f"Max PSI: {max_psi:.4f}")
    
    # Severe drift should have high PSI
    assert max_psi > 0.25, f"PSI too low for severe drift: {max_psi}"
    print("✓ Test passed: Severe drift has high PSI")


if __name__ == "__main__":
    test_psi_clean_data()
    test_psi_severe_drift()
    print("\n✓ All PSI tests passed!")
