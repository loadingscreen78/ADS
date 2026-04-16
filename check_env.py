# save as: check_env.py
# run as: python check_env.py

def check_environment():
    print("=" * 50)
    print("ENVIRONMENT CHECK")
    print("=" * 50)

    # Check GPU
    try:
        import cudf
        import cuml
        df = cudf.DataFrame({"a": [1, 2, 3]})
        print(f"[OK] cuDF working — GPU mode")
        print(f"[OK] cuML version: {cuml.__version__}")
        GPU_AVAILABLE = True
    except ImportError:
        print("[WARN] cuDF not found — falling back to CPU pandas")
        print("[WARN] Install RAPIDS or use Google Colab with GPU runtime")
        GPU_AVAILABLE = False

    # Check MLflow
    try:
        import mlflow
        print(f"[OK] MLflow version: {mlflow.__version__}")
    except ImportError:
        print("[FAIL] MLflow not installed — run: pip install mlflow")

    # Check scipy (for KS test)
    try:
        from scipy.stats import ks_2samp
        print(f"[OK] scipy available — KS test ready")
    except ImportError:
        print("[FAIL] scipy not installed — run: pip install scipy")

    print("=" * 50)
    print(f"GPU MODE: {GPU_AVAILABLE}")
    print("=" * 50)
    return GPU_AVAILABLE

if __name__ == "__main__":
    check_environment()
