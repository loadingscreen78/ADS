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
