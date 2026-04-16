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
