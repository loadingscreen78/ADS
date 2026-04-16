# ML Auto Retraining & Monitoring System
## Complete Code Implementation Guide
### GPU-Accelerated · Docker · RAPIDS · MLflow

---

## WHERE TO START — Read This First

Build in this exact order. Each phase produces working, testable code before moving on.

```
Phase 0 → Environment Setup          (Day 1)
Phase 1 → Synthetic Data + Reference Store  (Day 2)
Phase 2 → Drift Detection Module     (Day 3-4)
Phase 3 → Docker Services            (Day 5)
Phase 4 → cuML Retraining Engine     (Day 6-7)
Phase 5 → CARA Scheduler             (Day 8)
Phase 6 → MLflow Integration         (Day 9)
Phase 7 → Wire Everything Together   (Day 10)
```

---

## PROJECT FOLDER STRUCTURE

```
ml-autoretrain/
│
├── data/
│   ├── reference/          ← training distribution snapshots
│   ├── production/         ← incoming batches (simulated)
│   └── models/             ← saved model artifacts
│
├── src/
│   ├── drift/
│   │   ├── __init__.py
│   │   ├── ks_detector.py
│   │   ├── psi_detector.py
│   │   ├── adversarial.py
│   │   └── drift_engine.py
│   │
│   ├── scheduler/
│   │   ├── __init__.py
│   │   └── cara.py
│   │
│   ├── retraining/
│   │   ├── __init__.py
│   │   ├── retrain_engine.py
│   │   └── fairness_gate.py
│   │
│   ├── services/
│   │   ├── drift_monitor_service.py
│   │   └── retrain_service.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── data_generator.py
│       └── audit_logger.py
│
├── tests/
│   ├── test_ks.py
│   ├── test_psi.py
│   └── test_cara.py
│
├── docker/
│   ├── drift-monitor/
│   │   └── Dockerfile
│   └── retrain-engine/
│       └── Dockerfile
│
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## PHASE 0 — ENVIRONMENT SETUP

### Step 1: Install Dependencies

```bash
# Create project folder
mkdir ml-autoretrain && cd ml-autoretrain

# If you have an NVIDIA GPU (Google Colab T4, local GPU)
pip install cudf-cu12==26.2.0 cuml-cu12==26.2.0 \
    --extra-index-url=https://pypi.nvidia.com

# If NO GPU available — use CPU fallback for development
pip install pandas numpy scipy scikit-learn

# Common packages always needed
pip install mlflow==2.19.0 \
            fastapi==0.115.0 \
            uvicorn==0.34.0 \
            requests==2.32.0 \
            pyarrow==18.0.0 \
            joblib==1.4.2 \
            python-dotenv==1.0.1

# Install Docker Desktop from: https://docs.docker.com/get-docker/
```

### Step 2: Verify GPU Access

```python
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
```

```bash
python check_env.py
```

---

## PHASE 1 — SYNTHETIC DATA + REFERENCE STORE

This creates fake production data so you can test everything without a real dataset.

```python
# src/utils/data_generator.py

import numpy as np
import os

# Use cuDF if GPU available, else pandas
try:
    import cudf as pd_lib
    GPU = True
except ImportError:
    import pandas as pd_lib
    GPU = False

import pandas as pd  # always need real pandas for some ops


class DataGenerator:
    """
    Generates synthetic credit card transaction data.
    Used to simulate real production data for testing.
    Features mimic real fraud detection datasets.
    """

    FEATURES = [
        "amount",           # Transaction amount in USD
        "hour_of_day",      # 0-23
        "day_of_week",      # 0-6
        "merchant_category",# 0-9 (encoded)
        "user_age_bucket",  # 0-5 (encoded age ranges)
        "transaction_count_7d",  # rolling 7-day count
        "avg_amount_30d",   # rolling 30-day average amount
        "distance_from_home",    # km from home location
        "is_international",      # 0 or 1
        "card_present",          # 0 or 1
    ]

    def generate_reference(self, n_rows: int = 100_000, seed: int = 42) -> pd.DataFrame:
        """
        Generate REFERENCE (training) distribution.
        This is what the model was trained on.
        Saved to disk as the baseline for drift detection.
        """
        np.random.seed(seed)
        data = {
            "amount":                np.random.exponential(scale=50,  size=n_rows).clip(1, 5000),
            "hour_of_day":           np.random.randint(0, 24,         size=n_rows).astype(float),
            "day_of_week":           np.random.randint(0, 7,          size=n_rows).astype(float),
            "merchant_category":     np.random.randint(0, 10,         size=n_rows).astype(float),
            "user_age_bucket":       np.random.randint(0, 6,          size=n_rows).astype(float),
            "transaction_count_7d":  np.random.poisson(lam=5,         size=n_rows).astype(float),
            "avg_amount_30d":        np.random.normal(loc=45, scale=20, size=n_rows).clip(1, 1000),
            "distance_from_home":    np.random.exponential(scale=10,  size=n_rows).clip(0, 500),
            "is_international":      np.random.binomial(1, p=0.08,    size=n_rows).astype(float),
            "card_present":          np.random.binomial(1, p=0.75,    size=n_rows).astype(float),
        }
        # Add binary label: ~3% fraud rate
        fraud_prob = (
            0.001 * data["amount"] / 100 +
            0.3 * data["is_international"] +
            0.1 * (1 - data["card_present"])
        )
        data["is_fraud"] = (np.random.random(n_rows) < fraud_prob.clip(0, 1)).astype(int)
        return pd.DataFrame(data)

    def generate_drifted(self, n_rows: int = 50_000, drift_level: str = "moderate") -> pd.DataFrame:
        """
        Generate DRIFTED production data.
        drift_level: 'none', 'moderate', 'severe'

        Simulates what happens when real-world behavior changes —
        e.g., post-pandemic spending shifts, new fraud patterns.
        """
        base = self.generate_reference(n_rows, seed=99)

        if drift_level == "none":
            return base

        elif drift_level == "moderate":
            # Simulate: amounts increased, more international transactions
            base["amount"] = base["amount"] * 1.4 + np.random.normal(0, 10, n_rows)
            base["is_international"] = np.random.binomial(1, p=0.18, size=n_rows).astype(float)
            base["merchant_category"] = np.random.randint(3, 10, size=n_rows).astype(float)

        elif drift_level == "severe":
            # Simulate: major behavioral shift — like a global event
            base["amount"] = np.random.exponential(scale=150, size=n_rows).clip(1, 10000)
            base["is_international"] = np.random.binomial(1, p=0.45, size=n_rows).astype(float)
            base["hour_of_day"] = np.random.choice([22, 23, 0, 1, 2], size=n_rows).astype(float)
            base["transaction_count_7d"] = np.random.poisson(lam=15, size=n_rows).astype(float)

        return base

    def save_reference(self, df: pd.DataFrame, path: str = "data/reference/reference.parquet"):
        """Save reference distribution to Parquet."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df.to_parquet(path, index=False)
        print(f"[OK] Reference saved: {path} ({len(df):,} rows, {len(df.columns)} features)")

    def save_production_batch(self, df: pd.DataFrame, batch_id: str,
                               path: str = "data/production/"):
        """Save a production batch to Parquet."""
        os.makedirs(path, exist_ok=True)
        out = os.path.join(path, f"batch_{batch_id}.parquet")
        df.to_parquet(out, index=False)
        print(f"[OK] Production batch saved: {out}")
        return out


# ── RUN THIS FIRST ──────────────────────────────────────────────────
if __name__ == "__main__":
    gen = DataGenerator()

    print("Generating reference distribution (100K rows)...")
    ref = gen.generate_reference(n_rows=100_000)
    gen.save_reference(ref)

    print("\nGenerating clean production batch (no drift)...")
    clean = gen.generate_drifted(n_rows=50_000, drift_level="none")
    gen.save_production_batch(clean, batch_id="001_clean")

    print("\nGenerating moderate drift batch...")
    moderate = gen.generate_drifted(n_rows=50_000, drift_level="moderate")
    gen.save_production_batch(moderate, batch_id="002_moderate")

    print("\nGenerating severe drift batch...")
    severe = gen.generate_drifted(n_rows=50_000, drift_level="severe")
    gen.save_production_batch(severe, batch_id="003_severe")

    print("\nData generation complete.")
    print(f"Reference columns: {list(ref.columns)}")
    print(f"Reference shape: {ref.shape}")
    print(f"Fraud rate: {ref['is_fraud'].mean():.2%}")
```

```bash
python src/utils/data_generator.py
```

**Expected output:**
```
[OK] Reference saved: data/reference/reference.parquet (100,000 rows, 11 features)
[OK] Production batch saved: data/production/batch_001_clean.parquet
[OK] Production batch saved: data/production/batch_002_moderate.parquet
[OK] Production batch saved: data/production/batch_003_severe.parquet
```

---

## PHASE 2 — DRIFT DETECTION MODULE

### 2A — KS Test Detector

```python
# src/drift/ks_detector.py

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from dataclasses import dataclass
from typing import Dict, List
import time

# GPU/CPU switch — works both ways
try:
    import cudf
    GPU = True
    print("[INFO] KS Detector: GPU mode (cuDF)")
except ImportError:
    GPU = False
    print("[INFO] KS Detector: CPU mode (pandas)")


@dataclass
class KSResult:
    """Result for one feature's KS test."""
    feature:    str
    statistic:  float   # max difference between CDFs (0–1)
    p_value:    float   # probability distributions are same
    drifted:    bool    # True if p < threshold
    severity:   str     # "none", "moderate", "severe"


class KSDriftDetector:
    """
    Kolmogorov-Smirnov drift detector.

    Compares the cumulative distribution of each feature
    between reference (training) data and production data.

    KS Statistic: maximum vertical distance between two ECDFs
    p-value < 0.05 means the distributions are statistically different.

    Usage:
        detector = KSDriftDetector("data/reference/reference.parquet")
        results  = detector.detect("data/production/batch_001.parquet")
        report   = detector.report(results)
    """

    def __init__(self, reference_path: str, p_threshold: float = 0.05,
                 features: List[str] = None):
        self.p_threshold = p_threshold

        # Load reference data
        if GPU:
            self.ref_df = cudf.read_parquet(reference_path).to_pandas()
        else:
            self.ref_df = pd.read_parquet(reference_path)

        # Features to monitor (exclude label column)
        self.features = features or [
            c for c in self.ref_df.columns if c != "is_fraud"
        ]
        print(f"[KS] Loaded reference: {len(self.ref_df):,} rows, "
              f"monitoring {len(self.features)} features")

    def detect(self, production_path: str) -> Dict[str, KSResult]:
        """
        Run KS test on every monitored feature.

        Returns dict: feature_name → KSResult
        """
        t_start = time.time()

        # Load production data
        if GPU:
            prod_df = cudf.read_parquet(production_path).to_pandas()
        else:
            prod_df = pd.read_parquet(production_path)

        results = {}
        for feature in self.features:
            if feature not in prod_df.columns:
                print(f"[WARN] Feature '{feature}' missing from production data")
                continue

            ref_vals  = self.ref_df[feature].dropna().values
            prod_vals = prod_df[feature].dropna().values

            # THE CORE COMPUTATION
            stat, p_val = ks_2samp(ref_vals, prod_vals)

            # Classify severity
            if p_val >= self.p_threshold:
                severity = "none"
            elif stat < 0.1:
                severity = "low"
            elif stat < 0.2:
                severity = "moderate"
            else:
                severity = "severe"

            results[feature] = KSResult(
                feature   = feature,
                statistic = round(float(stat),   4),
                p_value   = round(float(p_val),  4),
                drifted   = bool(p_val < self.p_threshold),
                severity  = severity,
            )

        elapsed = time.time() - t_start
        n_drifted = sum(1 for r in results.values() if r.drifted)
        print(f"[KS] Computed {len(results)} features in {elapsed:.2f}s — "
              f"{n_drifted}/{len(results)} drifted")
        return results

    def report(self, results: Dict[str, KSResult]) -> None:
        """Pretty-print the drift report."""
        print("\n" + "=" * 60)
        print("KS DRIFT REPORT")
        print("=" * 60)
        print(f"{'Feature':<28} {'Stat':>6} {'p-val':>8} {'Drifted':>8} {'Severity':>10}")
        print("-" * 60)
        for feat, r in sorted(results.items(),
                               key=lambda x: x[1].statistic, reverse=True):
            flag = "YES ⚠" if r.drifted else "no"
            print(f"{feat:<28} {r.statistic:>6.4f} {r.p_value:>8.4f} "
                  f"{flag:>8} {r.severity:>10}")
        print("=" * 60)

        drifted = [f for f, r in results.items() if r.drifted]
        print(f"\nDrifted features ({len(drifted)}/{len(results)}): {drifted}")


# ── TEST THIS MODULE ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n=== Testing KS Detector on CLEAN data ===")
    detector = KSDriftDetector("data/reference/reference.parquet")
    results  = detector.detect("data/production/batch_001_clean.parquet")
    detector.report(results)

    print("\n\n=== Testing KS Detector on MODERATE DRIFT data ===")
    results2 = detector.detect("data/production/batch_002_moderate.parquet")
    detector.report(results2)

    print("\n\n=== Testing KS Detector on SEVERE DRIFT data ===")
    results3 = detector.detect("data/production/batch_003_severe.parquet")
    detector.report(results3)
```

```bash
python src/drift/ks_detector.py
```

---

### 2B — PSI Detector

```python
# src/drift/psi_detector.py

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, List, Optional
import time

try:
    import cupy as cp
    import cudf
    GPU = True
    print("[INFO] PSI Detector: GPU mode (cuPy + cuDF)")
except ImportError:
    GPU = False
    print("[INFO] PSI Detector: CPU mode (numpy)")


@dataclass
class PSIResult:
    """Result for one feature's PSI computation."""
    feature:    str
    psi:        float   # Population Stability Index value
    severity:   str     # "none", "low", "moderate", "significant"
    drifted:    bool    # True if psi > threshold (default 0.25)
    ref_mean:   float
    prod_mean:  float
    mean_shift: float   # (prod_mean - ref_mean) / ref_mean * 100 %


class PSIDriftDetector:
    """
    Population Stability Index (PSI) Drift Detector.

    PSI measures HOW MUCH a feature distribution has shifted.
    Unlike KS test, PSI gives a magnitude of shift — very useful
    for deciding whether to retrain and how urgently.

    PSI Thresholds (industry standard, from risk scorecard monitoring):
        PSI < 0.10  → No significant shift
        PSI 0.10–0.25 → Moderate shift — investigate
        PSI > 0.25  → Significant shift — action required

    Formula:
        PSI = Σ (prod_pct - ref_pct) × ln(prod_pct / ref_pct)
        where percentages are computed per histogram bin.
    """

    # PSI thresholds (industry standard)
    THRESHOLD_LOW         = 0.10
    THRESHOLD_MODERATE    = 0.25  # alert threshold
    THRESHOLD_SIGNIFICANT = 0.50  # critical threshold

    def __init__(self, reference_path: str, bins: int = 10,
                 features: Optional[List[str]] = None):
        self.bins = bins

        if GPU:
            self.ref_df = cudf.read_parquet(reference_path).to_pandas()
        else:
            self.ref_df = pd.read_parquet(reference_path)

        self.features = features or [
            c for c in self.ref_df.columns if c != "is_fraud"
        ]

        # Pre-compute bin edges from reference distribution for each feature
        # This is important: bin edges MUST come from reference, not production
        self._bin_edges = {}
        for feat in self.features:
            vals = self.ref_df[feat].dropna().values
            self._bin_edges[feat] = np.percentile(
                vals, np.linspace(0, 100, self.bins + 1)
            )

        print(f"[PSI] Loaded reference: {len(self.ref_df):,} rows, "
              f"{self.bins} bins per feature")

    def _compute_psi_single(self, ref_vals: np.ndarray,
                             prod_vals: np.ndarray,
                             bin_edges: np.ndarray) -> float:
        """
        Compute PSI for one feature.

        Steps:
        1. Bin both distributions using SAME bin edges (from reference)
        2. Convert bin counts to percentages
        3. Apply PSI formula: Σ (prod% - ref%) × ln(prod% / ref%)
        """
        epsilon = 1e-6  # avoid log(0)

        # Bin counts using reference bin edges
        ref_counts,  _ = np.histogram(ref_vals,  bins=bin_edges)
        prod_counts, _ = np.histogram(prod_vals, bins=bin_edges)

        # Convert to percentages (add epsilon to avoid division by zero)
        ref_pct  = (ref_counts  / len(ref_vals))  + epsilon
        prod_pct = (prod_counts / len(prod_vals)) + epsilon

        # Normalize so they sum to 1 (after epsilon, they might not)
        ref_pct  = ref_pct  / ref_pct.sum()
        prod_pct = prod_pct / prod_pct.sum()

        # PSI formula
        psi = float(np.sum((prod_pct - ref_pct) * np.log(prod_pct / ref_pct)))
        return psi

    def detect(self, production_path: str) -> Dict[str, PSIResult]:
        """Compute PSI for all features."""
        t_start = time.time()

        if GPU:
            prod_df = cudf.read_parquet(production_path).to_pandas()
        else:
            prod_df = pd.read_parquet(production_path)

        results = {}
        for feat in self.features:
            if feat not in prod_df.columns:
                continue

            ref_vals  = self.ref_df[feat].dropna().values.astype(float)
            prod_vals = prod_df[feat].dropna().values.astype(float)

            psi = self._compute_psi_single(ref_vals, prod_vals,
                                            self._bin_edges[feat])

            # Classify
            if psi < self.THRESHOLD_LOW:
                severity = "none"
            elif psi < self.THRESHOLD_MODERATE:
                severity = "moderate"
            elif psi < self.THRESHOLD_SIGNIFICANT:
                severity = "significant"
            else:
                severity = "critical"

            ref_mean  = float(np.mean(ref_vals))
            prod_mean = float(np.mean(prod_vals))
            mean_shift = ((prod_mean - ref_mean) / (ref_mean + 1e-9)) * 100

            results[feat] = PSIResult(
                feature    = feat,
                psi        = round(psi, 4),
                severity   = severity,
                drifted    = psi > self.THRESHOLD_MODERATE,
                ref_mean   = round(ref_mean, 4),
                prod_mean  = round(prod_mean, 4),
                mean_shift = round(mean_shift, 2),
            )

        elapsed = time.time() - t_start
        n_drifted = sum(1 for r in results.values() if r.drifted)
        print(f"[PSI] Computed {len(results)} features in {elapsed:.2f}s — "
              f"{n_drifted}/{len(results)} drifted")
        return results

    def report(self, results: Dict[str, PSIResult]) -> None:
        print("\n" + "=" * 70)
        print("PSI DRIFT REPORT")
        print("=" * 70)
        print(f"{'Feature':<28} {'PSI':>6} {'Severity':>12} "
              f"{'Drifted':>8} {'Mean Shift':>12}")
        print("-" * 70)
        for feat, r in sorted(results.items(),
                               key=lambda x: x[1].psi, reverse=True):
            flag = "YES ⚠" if r.drifted else "no"
            print(f"{feat:<28} {r.psi:>6.4f} {r.severity:>12} "
                  f"{flag:>8} {r.mean_shift:>+11.1f}%")
        print("=" * 70)


# ── TEST ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n=== PSI on CLEAN data ===")
    psi = PSIDriftDetector("data/reference/reference.parquet")
    r1  = psi.detect("data/production/batch_001_clean.parquet")
    psi.report(r1)

    print("\n=== PSI on SEVERE DRIFT data ===")
    r3 = psi.detect("data/production/batch_003_severe.parquet")
    psi.report(r3)
```

---

### 2C — Unified Drift Engine

```python
# src/drift/drift_engine.py
"""
Combines KS + PSI into a single DriftEngine class.
This is what the monitoring service calls every batch.
"""

import json
import time
from datetime import datetime
from typing import Dict, Any

from src.drift.ks_detector  import KSDriftDetector,  KSResult
from src.drift.psi_detector import PSIDriftDetector, PSIResult


class DriftScore:
    """Aggregated drift score from all detectors for one batch."""

    def __init__(self, batch_id: str, ks_results: Dict[str, KSResult],
                 psi_results: Dict[str, PSIResult]):
        self.batch_id    = batch_id
        self.timestamp   = datetime.utcnow().isoformat()
        self.ks_results  = ks_results
        self.psi_results = psi_results

        # Compute aggregate scores
        self.n_features   = len(ks_results)
        self.ks_drifted   = [f for f, r in ks_results.items()  if r.drifted]
        self.psi_drifted  = [f for f, r in psi_results.items() if r.drifted]

        # Features drifted by BOTH detectors = confirmed drift
        self.confirmed_drift = list(
            set(self.ks_drifted) & set(self.psi_drifted)
        )

        # Overall drift ratio (0.0 – 1.0)
        self.drift_ratio = len(self.confirmed_drift) / max(self.n_features, 1)

        # Overall severity
        psi_vals = [r.psi for r in psi_results.values()]
        self.max_psi = max(psi_vals) if psi_vals else 0.0
        self.avg_psi = sum(psi_vals) / len(psi_vals) if psi_vals else 0.0

        if self.drift_ratio > 0.5 or self.max_psi > 0.5:
            self.overall_severity = "CRITICAL"
        elif self.drift_ratio > 0.25 or self.max_psi > 0.25:
            self.overall_severity = "SIGNIFICANT"
        elif self.drift_ratio > 0.1:
            self.overall_severity = "MODERATE"
        else:
            self.overall_severity = "NONE"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "batch_id":        self.batch_id,
            "timestamp":       self.timestamp,
            "n_features":      self.n_features,
            "ks_drifted":      self.ks_drifted,
            "psi_drifted":     self.psi_drifted,
            "confirmed_drift": self.confirmed_drift,
            "drift_ratio":     round(self.drift_ratio, 4),
            "max_psi":         round(self.max_psi,     4),
            "avg_psi":         round(self.avg_psi,     4),
            "overall_severity": self.overall_severity,
        }

    def __repr__(self):
        return (f"DriftScore(batch={self.batch_id}, "
                f"severity={self.overall_severity}, "
                f"confirmed={self.confirmed_drift}, "
                f"drift_ratio={self.drift_ratio:.2f})")


class DriftEngine:
    """
    Main drift detection engine.
    Runs KS + PSI on every incoming production batch.
    Returns a DriftScore that the CARA scheduler uses.
    """

    def __init__(self, reference_path: str):
        print("[DriftEngine] Initializing...")
        self.ks  = KSDriftDetector(reference_path)
        self.psi = PSIDriftDetector(reference_path)
        print("[DriftEngine] Ready.")

    def analyze_batch(self, batch_path: str, batch_id: str) -> DriftScore:
        """
        Run full drift analysis on a production batch.
        Returns DriftScore with aggregate results.
        """
        print(f"\n[DriftEngine] Analyzing batch: {batch_id}")
        t0 = time.time()

        ks_results  = self.ks.detect(batch_path)
        psi_results = self.psi.detect(batch_path)

        score = DriftScore(batch_id, ks_results, psi_results)

        elapsed = time.time() - t0
        print(f"[DriftEngine] Done in {elapsed:.2f}s — {score}")
        return score


# ── TEST ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    engine = DriftEngine("data/reference/reference.parquet")

    print("\n" + "="*50)
    print("BATCH 1: Clean (no drift expected)")
    s1 = engine.analyze_batch("data/production/batch_001_clean.parquet",    "001")
    print(json.dumps(s1.to_dict(), indent=2))

    print("\n" + "="*50)
    print("BATCH 2: Moderate drift")
    s2 = engine.analyze_batch("data/production/batch_002_moderate.parquet", "002")
    print(json.dumps(s2.to_dict(), indent=2))

    print("\n" + "="*50)
    print("BATCH 3: Severe drift")
    s3 = engine.analyze_batch("data/production/batch_003_severe.parquet",   "003")
    print(json.dumps(s3.to_dict(), indent=2))
```

```bash
python src/drift/drift_engine.py
```

---

## PHASE 3 — CARA SCHEDULER

```python
# src/scheduler/cara.py
"""
CARA — Cost-Aware Retraining Algorithm
Based on: Mahadevan & Mathioudakis, ScienceDirect 2024

Decides WHETHER to retrain and HOW (full vs incremental).
Balances accuracy gain vs GPU compute cost vs data quality.
"""

import json
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from src.drift.drift_engine import DriftScore


class RetrainDecision(Enum):
    FULL_RETRAIN  = "FULL_RETRAIN"   # full retraining from scratch
    INCREMENTAL   = "INCREMENTAL"    # retrain on recent data only
    DEFER         = "DEFER"          # check again next cycle
    NO_ACTION     = "NO_ACTION"      # no retraining needed


@dataclass
class CARAOutput:
    """Output of the CARA decision."""
    decision:         RetrainDecision
    score:            float       # CARA decision score (0–1)
    expected_gain:    float       # estimated accuracy gain
    compute_cost:     float       # normalized GPU cost (0–1)
    data_quality:     float       # quality score of new data (0–1)
    justification:    str         # human-readable reason
    timestamp:        str         # ISO timestamp


class CARAScheduler:
    """
    Cost-Aware Retraining Algorithm (CARA).

    Decision formula:
        score = (Δacc × data_quality × urgency_factor) / (compute_cost + ε)

    Decision thresholds:
        score > 0.7  → FULL_RETRAIN
        score 0.4–0.7 → INCREMENTAL
        score 0.2–0.4 → DEFER
        score < 0.2  → NO_ACTION

    Inputs:
        drift_score    : DriftScore from DriftEngine
        current_acc    : current model accuracy on validation set
        baseline_acc   : model accuracy at training time
        gpu_cost_per_hr: cost in USD per GPU hour (e.g., 0.5 for T4)
        retrain_time_hr: estimated retraining time in hours
        data_quality   : quality score 0–1 (1 = perfect data)
    """

    # Decision thresholds
    FULL_RETRAIN_THRESHOLD = 0.70
    INCREMENTAL_THRESHOLD  = 0.40
    DEFER_THRESHOLD        = 0.20

    # Safety floor: force retrain if accuracy drops below this
    SAFETY_FLOOR_DROP      = 0.07  # 7% below baseline = forced retrain

    def __init__(self, gpu_cost_per_hr: float = 0.5,
                 retrain_time_hr: float = 0.2):
        self.gpu_cost_per_hr = gpu_cost_per_hr
        self.retrain_time_hr = retrain_time_hr
        self.history = []  # log of past decisions

    def _estimate_accuracy_gain(self, drift_score: DriftScore,
                                 current_acc: float,
                                 baseline_acc: float) -> float:
        """
        Estimate expected accuracy gain from retraining.

        Higher drift ratio + larger accuracy drop = larger expected gain.
        This is a heuristic — in production you'd use historical data
        from past retrain events logged in MLflow.
        """
        acc_drop    = max(0, baseline_acc - current_acc)
        drift_boost = drift_score.drift_ratio * 0.05  # 5% max from drift alone
        expected_gain = acc_drop * 0.7 + drift_boost  # recover 70% of drop
        return min(expected_gain, 0.15)  # cap at 15% improvement

    def _compute_cost_score(self) -> float:
        """Normalized compute cost (0–1, higher = more expensive)."""
        raw_cost = self.gpu_cost_per_hr * self.retrain_time_hr
        return min(raw_cost / 2.0, 1.0)  # normalize: $2 = max

    def decide(self,
               drift_score:   DriftScore,
               current_acc:   float = 0.92,
               baseline_acc:  float = 0.95,
               data_quality:  float = 0.85) -> CARAOutput:
        """
        Make retraining decision.

        Args:
            drift_score   : output from DriftEngine.analyze_batch()
            current_acc   : current production accuracy (from monitoring)
            baseline_acc  : accuracy at deployment time
            data_quality  : quality of new data (0–1, e.g., from validation)
        """
        from datetime import datetime

        # ── Safety check: forced retrain if accuracy drop is severe ──
        acc_drop = baseline_acc - current_acc
        if acc_drop > self.SAFETY_FLOOR_DROP:
            return CARAOutput(
                decision      = RetrainDecision.FULL_RETRAIN,
                score         = 1.0,
                expected_gain = acc_drop,
                compute_cost  = self._compute_cost_score(),
                data_quality  = data_quality,
                justification = (
                    f"SAFETY OVERRIDE: Accuracy dropped {acc_drop:.1%} "
                    f"(> {self.SAFETY_FLOOR_DROP:.1%} floor). "
                    f"Forced full retrain regardless of cost."
                ),
                timestamp = datetime.utcnow().isoformat(),
            )

        # ── No drift: no action ──
        if drift_score.overall_severity == "NONE":
            return CARAOutput(
                decision      = RetrainDecision.NO_ACTION,
                score         = 0.0,
                expected_gain = 0.0,
                compute_cost  = self._compute_cost_score(),
                data_quality  = data_quality,
                justification = (
                    f"No significant drift detected "
                    f"(drift_ratio={drift_score.drift_ratio:.3f}, "
                    f"max_psi={drift_score.max_psi:.3f}). No action needed."
                ),
                timestamp = datetime.utcnow().isoformat(),
            )

        # ── Compute CARA score ──
        expected_gain = self._estimate_accuracy_gain(
            drift_score, current_acc, baseline_acc)
        compute_cost  = self._compute_cost_score()

        # Urgency factor: higher for critical/significant drift
        urgency_map = {"CRITICAL": 1.0, "SIGNIFICANT": 0.8, "MODERATE": 0.5}
        urgency = urgency_map.get(drift_score.overall_severity, 0.3)

        epsilon = 1e-6
        cara_score = (expected_gain * data_quality * urgency) / (compute_cost + epsilon)
        cara_score = min(cara_score, 1.0)  # cap at 1.0

        # ── Map score to decision ──
        if cara_score >= self.FULL_RETRAIN_THRESHOLD:
            decision = RetrainDecision.FULL_RETRAIN
            justification = (
                f"CARA score {cara_score:.3f} ≥ {self.FULL_RETRAIN_THRESHOLD}. "
                f"Drift severity: {drift_score.overall_severity}. "
                f"Expected gain: {expected_gain:.2%}. "
                f"Drifted features: {drift_score.confirmed_drift}. "
                f"Full retrain justified."
            )
        elif cara_score >= self.INCREMENTAL_THRESHOLD:
            decision = RetrainDecision.INCREMENTAL
            justification = (
                f"CARA score {cara_score:.3f} in incremental range. "
                f"Drift detected but compute cost not justified for full retrain. "
                f"Incremental update on recent {drift_score.confirmed_drift}."
            )
        elif cara_score >= self.DEFER_THRESHOLD:
            decision = RetrainDecision.DEFER
            justification = (
                f"CARA score {cara_score:.3f} below threshold. "
                f"Drift signal weak. Deferring — will re-check next cycle."
            )
        else:
            decision = RetrainDecision.NO_ACTION
            justification = (
                f"CARA score {cara_score:.3f} too low. "
                f"Expected gain ({expected_gain:.2%}) does not justify "
                f"GPU cost. No action."
            )

        output = CARAOutput(
            decision      = decision,
            score         = round(cara_score, 4),
            expected_gain = round(expected_gain, 4),
            compute_cost  = round(compute_cost, 4),
            data_quality  = data_quality,
            justification = justification,
            timestamp     = datetime.utcnow().isoformat(),
        )
        self.history.append(output)
        return output

    def print_decision(self, output: CARAOutput) -> None:
        print("\n" + "=" * 60)
        print("CARA DECISION")
        print("=" * 60)
        print(f"Decision:      {output.decision.value}")
        print(f"CARA Score:    {output.score:.4f}")
        print(f"Expected Gain: {output.expected_gain:.2%}")
        print(f"Compute Cost:  {output.compute_cost:.4f}")
        print(f"Data Quality:  {output.data_quality:.2f}")
        print(f"Timestamp:     {output.timestamp}")
        print(f"\nJustification:\n  {output.justification}")
        print("=" * 60)


# ── TEST ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from src.drift.drift_engine import DriftEngine

    engine = DriftEngine("data/reference/reference.parquet")
    cara   = CARAScheduler(gpu_cost_per_hr=0.5, retrain_time_hr=0.1)

    # Scenario 1: Clean batch — should be NO_ACTION
    print("\n--- Scenario 1: Clean batch ---")
    score1 = engine.analyze_batch("data/production/batch_001_clean.parquet", "001")
    out1   = cara.decide(score1, current_acc=0.94, baseline_acc=0.95)
    cara.print_decision(out1)

    # Scenario 2: Moderate drift
    print("\n--- Scenario 2: Moderate drift ---")
    score2 = engine.analyze_batch("data/production/batch_002_moderate.parquet", "002")
    out2   = cara.decide(score2, current_acc=0.91, baseline_acc=0.95)
    cara.print_decision(out2)

    # Scenario 3: Severe drift
    print("\n--- Scenario 3: Severe drift ---")
    score3 = engine.analyze_batch("data/production/batch_003_severe.parquet", "003")
    out3   = cara.decide(score3, current_acc=0.87, baseline_acc=0.95)
    cara.print_decision(out3)

    # Scenario 4: Safety floor triggered
    print("\n--- Scenario 4: Safety floor (accuracy collapse) ---")
    out4 = cara.decide(score1, current_acc=0.82, baseline_acc=0.95)
    cara.print_decision(out4)
```

```bash
python src/scheduler/cara.py
```

---

## PHASE 4 — cuML RETRAINING ENGINE

```python
# src/retraining/retrain_engine.py

import os
import time
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Tuple, Dict, Any

# GPU/CPU switch
try:
    import cudf
    import cuml
    from cuml.ensemble import RandomForestClassifier
    from cuml.model_selection import train_test_split
    from cuml.metrics import accuracy_score
    GPU = True
    print("[INFO] RetrainEngine: GPU mode (cuML)")
except ImportError:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
    GPU = False
    print("[INFO] RetrainEngine: CPU mode (sklearn)")


class RetrainEngine:
    """
    GPU-accelerated model retraining using cuML.

    On GPU: Uses cuML RandomForestClassifier
            → 10–50× faster than sklearn on large datasets
    On CPU: Falls back to sklearn (identical API)

    Workflow:
        1. Load recent + reference data
        2. Preprocess (on GPU via cuDF)
        3. Train cuML model
        4. Evaluate on hold-out set
        5. Save artifact + return metrics
    """

    FEATURES = [
        "amount", "hour_of_day", "day_of_week", "merchant_category",
        "user_age_bucket", "transaction_count_7d", "avg_amount_30d",
        "distance_from_home", "is_international", "card_present",
    ]
    TARGET = "is_fraud"

    def __init__(self, models_dir: str = "data/models"):
        self.models_dir = models_dir
        os.makedirs(models_dir, exist_ok=True)

    def load_training_data(self, reference_path: str,
                           production_path: str,
                           mode: str = "full") -> pd.DataFrame:
        """
        Load training data.

        mode = "full"        → reference + all production data
        mode = "incremental" → only recent production data (sliding window)
        """
        ref  = pd.read_parquet(reference_path)
        prod = pd.read_parquet(production_path)

        if mode == "full":
            combined = pd.concat([ref, prod], ignore_index=True)
        else:
            combined = prod  # incremental: only recent data

        # Shuffle
        combined = combined.sample(frac=1, random_state=42).reset_index(drop=True)
        print(f"[Retrain] Training data: {len(combined):,} rows (mode={mode})")
        return combined

    def preprocess(self, df: pd.DataFrame) -> Tuple:
        """
        Preprocess data for training.
        Returns X (features), y (labels) — as GPU arrays if available.
        """
        # Drop any rows with NaN
        df = df.dropna(subset=self.FEATURES + [self.TARGET])

        X = df[self.FEATURES].astype(float)
        y = df[self.TARGET].astype(int)

        if GPU:
            X = cudf.from_pandas(X)
            y = cudf.from_pandas(y)

        return X, y

    def train(self, reference_path: str, production_path: str,
              mode: str = "full",
              n_estimators: int = 100,
              max_depth: int = 8) -> Dict[str, Any]:
        """
        Full training pipeline.

        Returns metrics dict with accuracy, training time, model path.
        """
        print(f"\n[Retrain] Starting {mode.upper()} retrain...")
        t_total = time.time()

        # ── Load data ──
        df = self.load_training_data(reference_path, production_path, mode)
        X, y = self.preprocess(df)

        # ── Split ──
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        print(f"[Retrain] Train: {len(X_train):,} | Test: {len(X_test):,}")

        # ── Train ──
        print(f"[Retrain] Training RandomForest "
              f"(n_estimators={n_estimators}, max_depth={max_depth})...")
        t_train = time.time()

        model = RandomForestClassifier(
            n_estimators = n_estimators,
            max_depth    = max_depth,
            random_state = 42,
        )
        model.fit(X_train, y_train)
        train_time = time.time() - t_train
        print(f"[Retrain] Training done in {train_time:.2f}s")

        # ── Evaluate ──
        y_pred = model.predict(X_test)

        if GPU:
            y_test_np = y_test.to_pandas().values
            y_pred_np = y_pred.to_pandas().values
        else:
            y_test_np = y_test.values
            y_pred_np = y_pred

        acc = float(accuracy_score(y_test_np, y_pred_np))
        print(f"[Retrain] Test accuracy: {acc:.4f}")

        # ── Fairness check (basic subgroup) ──
        fairness_results = self._fairness_check(df, model)

        # ── Save model ──
        timestamp  = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        model_path = os.path.join(
            self.models_dir, f"model_{mode}_{timestamp}.pkl"
        )
        joblib.dump(model, model_path)
        print(f"[Retrain] Model saved: {model_path}")

        metrics = {
            "accuracy":        round(acc, 4),
            "train_time_sec":  round(train_time, 2),
            "total_time_sec":  round(time.time() - t_total, 2),
            "n_train":         int(len(X_train)),
            "n_test":          int(len(X_test)),
            "mode":            mode,
            "model_path":      model_path,
            "timestamp":       timestamp,
            "gpu_used":        GPU,
            "n_estimators":    n_estimators,
            "max_depth":       max_depth,
            "fairness":        fairness_results,
        }

        print(f"\n[Retrain] Complete. Accuracy={acc:.4f}, "
              f"Time={train_time:.2f}s, GPU={GPU}")
        return metrics

    def _fairness_check(self, df: pd.DataFrame, model) -> Dict[str, float]:
        """
        Basic fairness: compute accuracy per age bucket subgroup.
        In production: use AI Fairness 360 for full fairness audit.
        """
        results = {}
        try:
            df_copy = df.dropna(subset=self.FEATURES + [self.TARGET]).copy()
            X_all   = df_copy[self.FEATURES].values.astype(float)
            y_all   = df_copy[self.TARGET].values.astype(int)

            if GPU:
                X_gpu  = cudf.from_pandas(pd.DataFrame(X_all, columns=self.FEATURES))
                y_pred = model.predict(X_gpu).to_pandas().values
            else:
                y_pred = model.predict(X_all)

            # Per age bucket accuracy
            for bucket in range(6):
                mask = df_copy["user_age_bucket"].values == bucket
                if mask.sum() < 10:
                    continue
                grp_acc = float(
                    (y_pred[mask] == y_all[mask]).mean()
                )
                results[f"age_bucket_{bucket}"] = round(grp_acc, 4)

            # Flag if any group is more than 5% below overall
            overall = float((y_pred == y_all).mean())
            results["overall"] = round(overall, 4)
            results["fairness_passed"] = all(
                v >= overall - 0.05
                for k, v in results.items()
                if k.startswith("age_bucket")
            )
        except Exception as e:
            results["error"] = str(e)
            results["fairness_passed"] = False

        return results


# ── TEST ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    engine = RetrainEngine()

    print("=== FULL RETRAIN TEST ===")
    metrics = engine.train(
        reference_path  = "data/reference/reference.parquet",
        production_path = "data/production/batch_002_moderate.parquet",
        mode            = "full",
        n_estimators    = 100,
        max_depth       = 8,
    )
    print("\nMetrics:")
    print(json.dumps(
        {k: v for k, v in metrics.items() if k != "model_path"},
        indent=2
    ))
```

---

## PHASE 5 — MLflow Integration

```python
# src/retraining/mlflow_retrain.py
"""
Wraps RetrainEngine with MLflow experiment tracking.
Every retrain is logged: params, metrics, model artifact, tags.
"""

import mlflow
import mlflow.sklearn
import json
import os
from src.retraining.retrain_engine import RetrainEngine
from src.drift.drift_engine        import DriftScore
from src.scheduler.cara            import CARAOutput, RetrainDecision

MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")


def retrain_with_mlflow(
    reference_path:  str,
    production_path: str,
    drift_score:     DriftScore,
    cara_output:     CARAOutput,
    experiment_name: str = "fraud-detector-autoretrain",
) -> dict:
    """
    Run retrain and log everything to MLflow.

    Args:
        reference_path  : path to reference parquet
        production_path : path to production batch parquet
        drift_score     : DriftScore from DriftEngine
        cara_output     : CARAOutput from CARAScheduler
        experiment_name : MLflow experiment name

    Returns:
        dict with mlflow_run_id, metrics, model_uri
    """

    mlflow.set_tracking_uri(MLFLOW_URI)
    mlflow.set_experiment(experiment_name)

    # Determine retrain mode from CARA decision
    mode = ("incremental"
            if cara_output.decision == RetrainDecision.INCREMENTAL
            else "full")

    engine = RetrainEngine()

    with mlflow.start_run(run_name=f"auto_retrain_{drift_score.batch_id}") as run:
        run_id = run.info.run_id

        # ── Log drift context ──
        mlflow.log_params({
            "batch_id":          drift_score.batch_id,
            "drift_severity":    drift_score.overall_severity,
            "drift_ratio":       drift_score.drift_ratio,
            "max_psi":           drift_score.max_psi,
            "confirmed_drift":   ",".join(drift_score.confirmed_drift),
            "cara_decision":     cara_output.decision.value,
            "cara_score":        cara_output.score,
            "retrain_mode":      mode,
            "gpu_cost_per_hr":   0.5,
        })

        # ── Run actual training ──
        metrics = engine.train(
            reference_path  = reference_path,
            production_path = production_path,
            mode            = mode,
        )

        # ── Log metrics ──
        mlflow.log_metrics({
            "accuracy":       metrics["accuracy"],
            "train_time_sec": metrics["train_time_sec"],
            "n_train":        metrics["n_train"],
            "n_test":         metrics["n_test"],
        })

        # ── Log fairness metrics ──
        fairness = metrics.get("fairness", {})
        for k, v in fairness.items():
            if isinstance(v, (int, float)):
                mlflow.log_metric(f"fairness_{k}", v)

        # ── Log tags ──
        mlflow.set_tags({
            "trigger":           "automated_drift",
            "drift_batch":       drift_score.batch_id,
            "fairness_passed":   str(fairness.get("fairness_passed", "unknown")),
            "cara_justification": cara_output.justification[:250],
        })

        # ── Log model ──
        import joblib
        model = joblib.load(metrics["model_path"])
        mlflow.sklearn.log_model(
            sk_model        = model,
            artifact_path   = "model",
            registered_model_name = "fraud-detector-autoretrain",
        )

        # ── Log audit JSON ──
        audit = {
            "run_id":           run_id,
            "batch_id":         drift_score.batch_id,
            "timestamp":        cara_output.timestamp,
            "trigger_reason":   drift_score.overall_severity,
            "drifted_features": drift_score.confirmed_drift,
            "cara_decision":    cara_output.decision.value,
            "cara_score":       cara_output.score,
            "justification":    cara_output.justification,
            "accuracy_before":  0.95,   # from production monitoring
            "accuracy_after":   metrics["accuracy"],
            "fairness":         fairness,
            "model_path":       metrics["model_path"],
        }
        audit_path = f"audit_retrain_{drift_score.batch_id}.json"
        with open(audit_path, "w") as f:
            json.dump(audit, f, indent=2)
        mlflow.log_artifact(audit_path)
        os.remove(audit_path)

        print(f"\n[MLflow] Run ID: {run_id}")
        print(f"[MLflow] Accuracy: {metrics['accuracy']:.4f}")
        print(f"[MLflow] View at: {MLFLOW_URI}/#/experiments/")

        return {
            "mlflow_run_id": run_id,
            "accuracy":      metrics["accuracy"],
            "model_uri":     f"models:/fraud-detector-autoretrain/latest",
            "audit":         audit,
        }
```

---

## PHASE 6 — DOCKER COMPOSE STACK

```bash
# Start MLflow server first (run in terminal)
mlflow server \
    --backend-store-uri sqlite:///mlflow.db \
    --default-artifact-root ./mlruns \
    --host 0.0.0.0 \
    --port 5000 &

echo "MLflow UI: http://localhost:5000"
```

```yaml
# docker-compose.yml
version: "3.8"

services:

  # ── MLflow Tracking Server ──────────────────────────────────────
  mlflow:
    image: python:3.11-slim
    ports:
      - "5000:5000"
    volumes:
      - ./mlruns:/mlruns
      - ./mlflow.db:/mlflow.db
    command: >
      sh -c "pip install mlflow==2.19.0 -q &&
             mlflow server
             --backend-store-uri sqlite:////mlflow.db
             --default-artifact-root /mlruns
             --host 0.0.0.0 --port 5000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ── Drift Monitor Service ───────────────────────────────────────
  drift-monitor:
    image: rapidsai/base:25.02-cuda12.0-py3.11
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility
      - MLFLOW_TRACKING_URI=http://mlflow:5000
      - REFERENCE_PATH=/data/reference/reference.parquet
      - PRODUCTION_PATH=/data/production
    volumes:
      - ./data:/data
      - ./src:/app/src
      - ./src/services/drift_monitor_service.py:/app/service.py
    ports:
      - "8001:8001"
    command: >
      sh -c "pip install scipy fastapi uvicorn pyarrow -q &&
             uvicorn service:app --host 0.0.0.0 --port 8001"
    depends_on:
      - mlflow

  # ── Retrain Engine Service ──────────────────────────────────────
  retrain-engine:
    image: rapidsai/base:25.02-cuda12.0-py3.11
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility
      - MLFLOW_TRACKING_URI=http://mlflow:5000
    volumes:
      - ./data:/data
      - ./src:/app/src
      - ./src/services/retrain_service.py:/app/service.py
    ports:
      - "8002:8002"
    command: >
      sh -c "pip install mlflow fastapi uvicorn scikit-learn joblib pyarrow -q &&
             uvicorn service:app --host 0.0.0.0 --port 8002"
    depends_on:
      - mlflow
```

**Note:** If you don't have a GPU, remove the `runtime: nvidia` line and the `NVIDIA_*` environment variables. Docker will use CPU automatically.

---

## PHASE 7 — MAIN PIPELINE ORCHESTRATOR

```python
# main_pipeline.py
"""
Master pipeline — wires everything together.
Run this to test the full end-to-end flow:
  Data → Drift Detection → CARA → Retrain → MLflow
"""

import sys
import json
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.data_generator    import DataGenerator
from src.drift.drift_engine      import DriftEngine
from src.scheduler.cara          import CARAScheduler, RetrainDecision
from src.retraining.retrain_engine import RetrainEngine


def run_pipeline(batch_path: str, batch_id: str,
                 current_accuracy: float = 0.92):
    """
    Run full pipeline on one production batch.

    Returns: dict with decision, metrics (if retrained)
    """
    print("\n" + "=" * 60)
    print(f"PIPELINE RUN — Batch: {batch_id}")
    print("=" * 60)

    REFERENCE = "data/reference/reference.parquet"

    # ── Step 1: Drift Detection ──────────────────────────────────
    print("\n[1/3] Running drift detection...")
    engine = DriftEngine(REFERENCE)
    drift  = engine.analyze_batch(batch_path, batch_id)

    print(f"\n  Drift Summary:")
    print(f"  Severity:         {drift.overall_severity}")
    print(f"  Drift ratio:      {drift.drift_ratio:.2%}")
    print(f"  Max PSI:          {drift.max_psi:.4f}")
    print(f"  Confirmed drift:  {drift.confirmed_drift}")

    # ── Step 2: CARA Decision ────────────────────────────────────
    print("\n[2/3] Running CARA scheduler...")
    cara    = CARAScheduler(gpu_cost_per_hr=0.5, retrain_time_hr=0.1)
    decision = cara.decide(
        drift_score  = drift,
        current_acc  = current_accuracy,
        baseline_acc = 0.95,
        data_quality = 0.88,
    )
    cara.print_decision(decision)

    result = {
        "batch_id":  batch_id,
        "drift":     drift.to_dict(),
        "decision":  decision.decision.value,
        "cara_score": decision.score,
        "retrained": False,
        "metrics":   None,
    }

    # ── Step 3: Retrain if needed ────────────────────────────────
    if decision.decision in (RetrainDecision.FULL_RETRAIN,
                              RetrainDecision.INCREMENTAL):
        print(f"\n[3/3] Retraining ({decision.decision.value})...")
        mode = ("incremental"
                if decision.decision == RetrainDecision.INCREMENTAL
                else "full")

        retrain_engine = RetrainEngine()
        metrics = retrain_engine.train(
            reference_path  = REFERENCE,
            production_path = batch_path,
            mode            = mode,
        )

        result["retrained"] = True
        result["metrics"]   = {
            "accuracy":       metrics["accuracy"],
            "train_time_sec": metrics["train_time_sec"],
            "fairness":       metrics["fairness"],
        }
        print(f"\n  Retrain complete.")
        print(f"  New accuracy: {metrics['accuracy']:.4f}")
        print(f"  Fairness passed: {metrics['fairness'].get('fairness_passed')}")
    else:
        print(f"\n[3/3] No retrain needed ({decision.decision.value})")

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print(json.dumps({
        k: v for k, v in result.items()
        if k not in ("drift",)
    }, indent=2))
    return result


if __name__ == "__main__":
    # ── First: Generate data ──
    print("Generating data...")
    gen = DataGenerator()
    ref = gen.generate_reference(100_000)
    gen.save_reference(ref)
    gen.save_production_batch(gen.generate_drifted(50_000, "none"),     "001_clean")
    gen.save_production_batch(gen.generate_drifted(50_000, "moderate"), "002_moderate")
    gen.save_production_batch(gen.generate_drifted(50_000, "severe"),   "003_severe")

    print("\n\n" + "#" * 60)
    print("# TEST 1: Clean batch (expect: NO_ACTION)")
    print("#" * 60)
    run_pipeline("data/production/batch_001_clean.parquet",    "001", current_accuracy=0.94)

    print("\n\n" + "#" * 60)
    print("# TEST 2: Moderate drift (expect: INCREMENTAL or DEFER)")
    print("#" * 60)
    run_pipeline("data/production/batch_002_moderate.parquet", "002", current_accuracy=0.91)

    print("\n\n" + "#" * 60)
    print("# TEST 3: Severe drift (expect: FULL_RETRAIN)")
    print("#" * 60)
    run_pipeline("data/production/batch_003_severe.parquet",   "003", current_accuracy=0.87)
```

---

## HOW TO RUN EVERYTHING — Step by Step

```bash
# ── 1. Setup project ──────────────────────────────────────────────
mkdir ml-autoretrain && cd ml-autoretrain
mkdir -p src/drift src/scheduler src/retraining src/utils src/services
mkdir -p data/reference data/production data/models
touch src/__init__.py src/drift/__init__.py
touch src/scheduler/__init__.py src/retraining/__init__.py
touch src/utils/__init__.py

# ── 2. Install packages ───────────────────────────────────────────
pip install pandas numpy scipy scikit-learn mlflow fastapi uvicorn \
            pyarrow joblib python-dotenv requests

# For GPU (Colab or NVIDIA GPU machine):
# pip install cudf-cu12==26.2.0 cuml-cu12==26.2.0 \
#     --extra-index-url=https://pypi.nvidia.com

# ── 3. Copy all code files from this guide into correct paths ──────
# (copy each code block into the file path shown at the top)

# ── 4. Check environment ──────────────────────────────────────────
python check_env.py

# ── 5. Generate data ──────────────────────────────────────────────
python src/utils/data_generator.py

# ── 6. Test individual modules ────────────────────────────────────
python src/drift/ks_detector.py
python src/drift/psi_detector.py
python src/drift/drift_engine.py
python src/scheduler/cara.py
python src/retraining/retrain_engine.py

# ── 7. Run full pipeline ──────────────────────────────────────────
python main_pipeline.py

# ── 8. Start MLflow UI (in separate terminal) ─────────────────────
mlflow server --backend-store-uri sqlite:///mlflow.db \
              --default-artifact-root ./mlruns \
              --host 0.0.0.0 --port 5000

# Open: http://localhost:5000

# ── 9. Start Docker stack (optional) ─────────────────────────────
docker compose up --build
```

---

## WHAT TO DO ON GOOGLE COLAB (No Local GPU)

```python
# Cell 1: Install
!pip install cudf-cu12==26.2.0 cuml-cu12==26.2.0 \
    --extra-index-url=https://pypi.nvidia.com -q
!pip install mlflow scipy pyarrow joblib -q

# Cell 2: Clone or create project structure
import os
os.makedirs("ml-autoretrain/src/drift",       exist_ok=True)
os.makedirs("ml-autoretrain/src/scheduler",   exist_ok=True)
os.makedirs("ml-autoretrain/src/retraining",  exist_ok=True)
os.makedirs("ml-autoretrain/src/utils",       exist_ok=True)
os.makedirs("ml-autoretrain/data/reference",  exist_ok=True)
os.makedirs("ml-autoretrain/data/production", exist_ok=True)
os.makedirs("ml-autoretrain/data/models",     exist_ok=True)
os.chdir("ml-autoretrain")

# Cell 3: Paste each code file using %%writefile magic
# %%writefile src/utils/data_generator.py
# ... (paste the DataGenerator code here)

# Cell 4: Run
!python src/utils/data_generator.py
!python src/drift/drift_engine.py
!python src/scheduler/cara.py
!python main_pipeline.py
```

---

## TESTING — Validate Your Implementation

```python
# tests/test_pipeline.py
"""Quick validation tests — run after building each module."""

import sys, os
sys.path.insert(0, "..")

def test_data_generator():
    from src.utils.data_generator import DataGenerator
    gen = DataGenerator()
    df  = gen.generate_reference(n_rows=1000)
    assert len(df) == 1000,              "Wrong row count"
    assert "is_fraud" in df.columns,     "Label column missing"
    assert df.isnull().sum().sum() == 0, "Unexpected NaNs"
    print("[PASS] DataGenerator")

def test_ks_detector():
    from src.drift.ks_detector import KSDriftDetector
    det = KSDriftDetector("data/reference/reference.parquet")
    res = det.detect("data/production/batch_001_clean.parquet")
    # Clean data: most features should NOT drift
    n_drifted = sum(1 for r in res.values() if r.drifted)
    assert n_drifted < 5, f"Too many drifted on clean data: {n_drifted}"
    print(f"[PASS] KS Detector (drifted={n_drifted}/10 on clean data)")

def test_psi_detector():
    from src.drift.psi_detector import PSIDriftDetector
    psi = PSIDriftDetector("data/reference/reference.parquet")
    res = psi.detect("data/production/batch_003_severe.parquet")
    # Severe data: most features SHOULD drift
    n_drifted = sum(1 for r in res.values() if r.drifted)
    assert n_drifted >= 2, f"PSI missed severe drift: {n_drifted} drifted"
    print(f"[PASS] PSI Detector (drifted={n_drifted}/10 on severe data)")

def test_cara():
    from src.drift.drift_engine import DriftEngine
    from src.scheduler.cara import CARAScheduler, RetrainDecision
    engine = DriftEngine("data/reference/reference.parquet")
    cara   = CARAScheduler()

    # Severe drift should trigger full retrain
    score  = engine.analyze_batch("data/production/batch_003_severe.parquet", "t1")
    out    = cara.decide(score, current_acc=0.87, baseline_acc=0.95)
    assert out.decision == RetrainDecision.FULL_RETRAIN, \
        f"Expected FULL_RETRAIN, got {out.decision}"
    print(f"[PASS] CARA Scheduler (severe → {out.decision.value})")

    # Clean data should be NO_ACTION
    score2 = engine.analyze_batch("data/production/batch_001_clean.parquet", "t2")
    out2   = cara.decide(score2, current_acc=0.94, baseline_acc=0.95)
    assert out2.decision in (RetrainDecision.NO_ACTION, RetrainDecision.DEFER), \
        f"Expected NO_ACTION/DEFER on clean data, got {out2.decision}"
    print(f"[PASS] CARA Scheduler (clean → {out2.decision.value})")

def test_retrain_engine():
    from src.retraining.retrain_engine import RetrainEngine
    engine  = RetrainEngine()
    metrics = engine.train(
        reference_path  = "data/reference/reference.parquet",
        production_path = "data/production/batch_002_moderate.parquet",
        mode            = "full",
        n_estimators    = 20,  # small for fast test
        max_depth       = 4,
    )
    assert metrics["accuracy"] > 0.5, "Accuracy too low — something wrong"
    assert os.path.exists(metrics["model_path"]), "Model file not saved"
    print(f"[PASS] RetrainEngine (accuracy={metrics['accuracy']:.4f})")

if __name__ == "__main__":
    print("Running all tests...\n")
    test_data_generator()
    test_ks_detector()
    test_psi_detector()
    test_cara()
    test_retrain_engine()
    print("\n[ALL TESTS PASSED]")
```

```bash
python tests/test_pipeline.py
```

---

## BUILD ORDER SUMMARY

| Step | File | Command | Expected Output |
|------|------|---------|----------------|
| 1 | `check_env.py` | `python check_env.py` | GPU/CPU mode confirmed |
| 2 | `data_generator.py` | `python src/utils/data_generator.py` | 4 parquet files created |
| 3 | `ks_detector.py` | `python src/drift/ks_detector.py` | KS report for 3 batches |
| 4 | `psi_detector.py` | `python src/drift/psi_detector.py` | PSI report for 3 batches |
| 5 | `drift_engine.py` | `python src/drift/drift_engine.py` | DriftScore JSON output |
| 6 | `cara.py` | `python src/scheduler/cara.py` | 4 CARA decisions printed |
| 7 | `retrain_engine.py` | `python src/retraining/retrain_engine.py` | Accuracy + model saved |
| 8 | `test_pipeline.py` | `python tests/test_pipeline.py` | All tests PASSED |
| 9 | `main_pipeline.py` | `python main_pipeline.py` | Full end-to-end run |
| 10 | MLflow UI | `mlflow server ...` | Dashboard at :5000 |
