"""
Diagnosis Engine - Root Cause Analysis
Based on SHML paper (arXiv:2411.00186)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

class IssueType(Enum):
    """Types of issues that can be diagnosed"""
    CONCEPT_DRIFT = "concept_drift"
    COVARIATE_DRIFT = "covariate_drift"
    PRIOR_DRIFT = "prior_drift"
    DATA_QUALITY = "data_quality"
    MODEL_DEGRADATION = "model_degradation"
    SYSTEM_PERFORMANCE = "system_performance"

@dataclass
class Diagnosis:
    """Diagnosis result"""
    issue_type: IssueType
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    root_cause: str
    affected_components: List[str]
    recommended_actions: List[str]
    confidence: float

class DiagnosisEngine:
    """
    Diagnoses root causes of pipeline issues
    
    Analyzes:
    - Drift patterns (concept, covariate, prior)
    - Data quality issues
    - Model performance degradation
    - System bottlenecks
    """
    
    def __init__(self):
        print("[DiagnosisEngine] Initialized")
    
    def diagnose(
        self,
        model_accuracy: float,
        baseline_accuracy: float,
        drift_ratio: float,
        drift_features: List[Dict],
        data_quality: float,
        error_rate: float = 0.0
    ) -> List[Diagnosis]:
        """
        Perform comprehensive diagnosis
        
        Returns:
            List of diagnosed issues with recommended actions
        """
        diagnoses = []
        
        # 1. Check for concept drift (relationship between features and target changed)
        accuracy_drop = baseline_accuracy - model_accuracy
        if accuracy_drop > 0.05 and drift_ratio > 0.25:
            diagnoses.append(Diagnosis(
                issue_type=IssueType.CONCEPT_DRIFT,
                severity="HIGH" if accuracy_drop > 0.10 else "MEDIUM",
                root_cause=f"Model accuracy dropped {accuracy_drop:.1%} with {drift_ratio:.1%} drift. "
                           f"The relationship between features and fraud has changed.",
                affected_components=["model", "predictions"],
                recommended_actions=[
                    "Retrain model with recent data",
                    "Consider feature engineering",
                    "Update decision thresholds"
                ],
                confidence=0.85
            ))
        
        # 2. Check for covariate drift (feature distributions changed)
        if drift_ratio > 0.30:
            high_drift_features = [f for f in drift_features if f.get('is_drifted', False)]
            diagnoses.append(Diagnosis(
                issue_type=IssueType.COVARIATE_DRIFT,
                severity="HIGH" if drift_ratio > 0.50 else "MEDIUM",
                root_cause=f"Feature distributions shifted significantly ({drift_ratio:.1%} drift). "
                           f"{len(high_drift_features)} features show high drift.",
                affected_components=["features", "preprocessing"],
                recommended_actions=[
                    "Update feature normalization",
                    "Retrain with recent data",
                    "Monitor high-drift features closely"
                ],
                confidence=0.90
            ))
        
        # 3. Check for prior drift (class distribution changed)
        # This would require comparing fraud rates, but we can infer from drift + stable accuracy
        if drift_ratio > 0.25 and accuracy_drop < 0.03:
            diagnoses.append(Diagnosis(
                issue_type=IssueType.PRIOR_DRIFT,
                severity="MEDIUM",
                root_cause="Class distribution may have shifted (fraud rate changed) "
                           "but model still performs reasonably.",
                affected_components=["data", "sampling"],
                recommended_actions=[
                    "Verify fraud rate in recent data",
                    "Adjust class weights if needed",
                    "Consider rebalancing strategy"
                ],
                confidence=0.70
            ))
        
        # 4. Check for data quality issues
        if data_quality < 0.80:
            diagnoses.append(Diagnosis(
                issue_type=IssueType.DATA_QUALITY,
                severity="HIGH" if data_quality < 0.70 else "MEDIUM",
                root_cause=f"Data quality score is low ({data_quality:.1%}). "
                           f"Missing values, outliers, or schema issues detected.",
                affected_components=["data", "preprocessing", "features"],
                recommended_actions=[
                    "Investigate data pipeline",
                    "Check for missing values",
                    "Validate data schema",
                    "Review data collection process"
                ],
                confidence=0.95
            ))
        
        # 5. Check for model degradation (accuracy drop without drift)
        if accuracy_drop > 0.05 and drift_ratio < 0.15:
            diagnoses.append(Diagnosis(
                issue_type=IssueType.MODEL_DEGRADATION,
                severity="HIGH",
                root_cause=f"Model accuracy dropped {accuracy_drop:.1%} without significant drift. "
                           f"Model may be overfitted or outdated.",
                affected_components=["model"],
                recommended_actions=[
                    "Retrain model from scratch",
                    "Review model architecture",
                    "Check for overfitting",
                    "Validate training data quality"
                ],
                confidence=0.80
            ))
        
        # 6. Check for system performance issues
        if error_rate > 0.10:
            diagnoses.append(Diagnosis(
                issue_type=IssueType.SYSTEM_PERFORMANCE,
                severity="CRITICAL" if error_rate > 0.20 else "HIGH",
                root_cause=f"High error rate ({error_rate:.1%}) indicates system issues. "
                           f"Predictions failing or timing out.",
                affected_components=["system", "infrastructure"],
                recommended_actions=[
                    "Check system resources",
                    "Review error logs",
                    "Optimize prediction pipeline",
                    "Scale infrastructure if needed"
                ],
                confidence=0.90
            ))
        
        return diagnoses
    
    def prioritize_actions(self, diagnoses: List[Diagnosis]) -> List[str]:
        """
        Prioritize recommended actions across all diagnoses
        
        Returns:
            Ordered list of actions to take
        """
        if not diagnoses:
            return []
        
        # Severity weights
        severity_weights = {
            "CRITICAL": 4,
            "HIGH": 3,
            "MEDIUM": 2,
            "LOW": 1
        }
        
        # Collect all actions with scores
        action_scores = {}
        for diag in diagnoses:
            weight = severity_weights.get(diag.severity, 1) * diag.confidence
            for action in diag.recommended_actions:
                if action not in action_scores:
                    action_scores[action] = 0
                action_scores[action] += weight
        
        # Sort by score
        prioritized = sorted(action_scores.items(), key=lambda x: x[1], reverse=True)
        
        return [action for action, score in prioritized]


# Test
if __name__ == "__main__":
    engine = DiagnosisEngine()
    
    print("\n=== Diagnosis Engine Test ===\n")
    
    # Simulate drift features
    drift_features = [
        {"feature": "amount", "is_drifted": True, "ks_statistic": 0.35},
        {"feature": "merchant_category", "is_drifted": True, "ks_statistic": 0.28},
        {"feature": "card_age_days", "is_drifted": False, "ks_statistic": 0.12},
    ]
    
    # Diagnose issues
    diagnoses = engine.diagnose(
        model_accuracy=0.88,
        baseline_accuracy=0.95,
        drift_ratio=0.55,
        drift_features=drift_features,
        data_quality=0.75,
        error_rate=0.05
    )
    
    print(f"Found {len(diagnoses)} issues:\n")
    
    for i, diag in enumerate(diagnoses, 1):
        print(f"{i}. {diag.issue_type.value.upper()} [{diag.severity}]")
        print(f"   Root Cause: {diag.root_cause}")
        print(f"   Affected: {', '.join(diag.affected_components)}")
        print(f"   Confidence: {diag.confidence:.0%}")
        print(f"   Actions:")
        for action in diag.recommended_actions:
            print(f"     - {action}")
        print()
    
    # Prioritized actions
    print("=== Prioritized Actions ===")
    actions = engine.prioritize_actions(diagnoses)
    for i, action in enumerate(actions, 1):
        print(f"{i}. {action}")
