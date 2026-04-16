#!/usr/bin/env python
"""
Verification script to check Day 1-5 implementation is complete
"""

import os
import sys


def check_file(path, description):
    """Check if a file exists"""
    exists = os.path.exists(path)
    status = "✓" if exists else "✗"
    print(f"  {status} {description}: {path}")
    return exists


def check_directory(path, description):
    """Check if a directory exists"""
    exists = os.path.isdir(path)
    status = "✓" if exists else "✗"
    print(f"  {status} {description}: {path}")
    return exists


def main():
    print("=" * 70)
    print("  ML AUTO-RETRAIN SYSTEM - SETUP VERIFICATION")
    print("=" * 70)
    
    all_checks = []
    
    # Core files
    print("\n📄 Core Files:")
    all_checks.append(check_file("requirements.txt", "Requirements file"))
    all_checks.append(check_file("check_env.py", "Environment checker"))
    all_checks.append(check_file("run_day1_to_day5.py", "Workflow script"))
    all_checks.append(check_file("docker-compose.yml", "Docker config"))
    all_checks.append(check_file("README.md", "README"))
    all_checks.append(check_file("QUICKSTART.md", "Quick start guide"))
    all_checks.append(check_file(".gitignore", "Git ignore"))
    
    # Directories
    print("\n📁 Directory Structure:")
    all_checks.append(check_directory("data/reference", "Reference data dir"))
    all_checks.append(check_directory("data/production", "Production data dir"))
    all_checks.append(check_directory("data/models", "Models dir"))
    all_checks.append(check_directory("src/drift", "Drift module"))
    all_checks.append(check_directory("src/scheduler", "Scheduler module"))
    all_checks.append(check_directory("src/retraining", "Retraining module"))
    all_checks.append(check_directory("src/utils", "Utils module"))
    all_checks.append(check_directory("tests", "Tests dir"))
    
    # Source files
    print("\n🐍 Source Code:")
    all_checks.append(check_file("src/__init__.py", "Main init"))
    all_checks.append(check_file("src/utils/data_generator.py", "Data generator"))
    all_checks.append(check_file("src/drift/ks_detector.py", "KS detector"))
    all_checks.append(check_file("src/drift/psi_detector.py", "PSI detector"))
    all_checks.append(check_file("src/drift/drift_engine.py", "Drift engine"))
    all_checks.append(check_file("src/scheduler/cara.py", "CARA scheduler"))
    
    # Test files
    print("\n🧪 Test Files:")
    all_checks.append(check_file("tests/test_ks.py", "KS tests"))
    all_checks.append(check_file("tests/test_psi.py", "PSI tests"))
    all_checks.append(check_file("tests/test_cara.py", "CARA tests"))
    
    # Summary
    print("\n" + "=" * 70)
    passed = sum(all_checks)
    total = len(all_checks)
    
    if passed == total:
        print(f"  ✅ ALL CHECKS PASSED ({passed}/{total})")
        print("=" * 70)
        print("\n🎉 Day 1-5 setup is complete!")
        print("\nNext steps:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Run workflow: python run_day1_to_day5.py")
        print("  3. Check QUICKSTART.md for detailed instructions")
        return 0
    else:
        print(f"  ⚠️  SOME CHECKS FAILED ({passed}/{total})")
        print("=" * 70)
        print("\n❌ Setup incomplete. Please review missing files above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
