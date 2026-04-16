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
