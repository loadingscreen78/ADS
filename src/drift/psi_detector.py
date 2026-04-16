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
