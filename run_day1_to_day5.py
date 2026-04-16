#!/usr/bin/env python
"""
ML Auto-Retrain System - Day 1 to Day 5 Complete Workflow
Executes all tasks from environment setup to CARA scheduler testing
"""

import os
import sys
import subprocess
import time


def print_header(text):
    """Print formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def run_command(cmd, description):
    """Run a Python script and handle errors"""
    print(f"→ {description}...")
    try:
        result = subprocess.run(
            [sys.executable, cmd],
            capture_output=False,
            text=True,
            check=True
        )
        print(f"✓ {description} completed successfully\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed with error code {e.returncode}\n")
        return False
    except Exception as e:
        print(f"✗ {description} failed: {str(e)}\n")
        return False


def main():
    print_header("ML AUTO-RETRAIN SYSTEM - DAY 1 TO DAY 5 WORKFLOW")
    
    start_time = time.time()
    
    # ═══════════════════════════════════════════════════════════════
    # DAY 1: ENVIRONMENT SETUP
    # ═══════════════════════════════════════════════════════════════
    print_header("DAY 1: ENVIRONMENT SETUP")
    
    print("Checking environment...")
    if not run_command("check_env.py", "Environment check"):
        print("⚠ Warning: Some dependencies may be missing")
        print("   Install with: pip install -r requirements.txt")
    
    # ═══════════════════════════════════════════════════════════════
    # DAY 2: SYNTHETIC DATA GENERATION
    # ═══════════════════════════════════════════════════════════════
    print_header("DAY 2: SYNTHETIC DATA GENERATION")
    
    if not run_command("src/utils/data_generator.py", "Generate synthetic data"):
        print("✗ Data generation failed. Cannot proceed.")
        return 1
    
    # Verify data files were created
    expected_files = [
        "data/reference/reference.parquet",
        "data/production/batch_001_clean.parquet",
        "data/production/batch_002_moderate.parquet",
        "data/production/batch_003_severe.parquet",
    ]
    
    missing_files = [f for f in expected_files if not os.path.exists(f)]
    if missing_files:
        print(f"✗ Missing data files: {missing_files}")
        return 1
    
    print("✓ All data files generated successfully")
    
    # ═══════════════════════════════════════════════════════════════
    # DAY 3-4: DRIFT DETECTION
    # ═══════════════════════════════════════════════════════════════
    print_header("DAY 3-4: DRIFT DETECTION MODULES")
    
    print("Testing KS Drift Detector...")
    if not run_command("src/drift/ks_detector.py", "KS Drift Detection"):
        print("⚠ KS detector test had issues")
    
    print("\nTesting PSI Drift Detector...")
    if not run_command("src/drift/psi_detector.py", "PSI Drift Detection"):
        print("⚠ PSI detector test had issues")
    
    print("\nTesting Unified Drift Engine...")
    if not run_command("src/drift/drift_engine.py", "Drift Engine"):
        print("⚠ Drift engine test had issues")
    
    # ═══════════════════════════════════════════════════════════════
    # DAY 5: CARA SCHEDULER
    # ═══════════════════════════════════════════════════════════════
    print_header("DAY 5: CARA SCHEDULER")
    
    if not run_command("src/scheduler/cara.py", "CARA Scheduler"):
        print("⚠ CARA scheduler test had issues")
    
    # ═══════════════════════════════════════════════════════════════
    # RUN UNIT TESTS
    # ═══════════════════════════════════════════════════════════════
    print_header("RUNNING UNIT TESTS")
    
    tests = [
        ("tests/test_ks.py", "KS Detector Tests"),
        ("tests/test_psi.py", "PSI Detector Tests"),
        ("tests/test_cara.py", "CARA Scheduler Tests"),
    ]
    
    test_results = []
    for test_file, test_name in tests:
        result = run_command(test_file, test_name)
        test_results.append((test_name, result))
    
    # ═══════════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════════
    elapsed = time.time() - start_time
    
    print_header("EXECUTION SUMMARY")
    
    print("Test Results:")
    for test_name, passed in test_results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {status}: {test_name}")
    
    print(f"\nTotal execution time: {elapsed:.2f} seconds")
    
    print("\n" + "=" * 70)
    print("  DAY 1-5 WORKFLOW COMPLETE!")
    print("=" * 70)
    
    print("\nNext Steps:")
    print("  • Day 6-7: Implement cuML Retraining Engine")
    print("  • Day 8: Wire CARA with Retraining")
    print("  • Day 9: MLflow Integration")
    print("  • Day 10: Docker Services & End-to-End Testing")
    
    print("\nDocker Services:")
    print("  • Start services: docker-compose up -d")
    print("  • MLflow UI: http://localhost:5000")
    print("  • Drift Monitor: http://localhost:8001")
    print("  • Retrain Engine: http://localhost:8002")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n✗ Workflow interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {str(e)}")
        sys.exit(1)
