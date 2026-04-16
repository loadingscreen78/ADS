"""
Health Monitor - Continuous Pipeline Monitoring
Based on SHML paper (arXiv:2411.00186)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
import numpy as np

@dataclass
class HealthMetrics:
    """Pipeline health metrics"""
    timestamp: str
    model_accuracy: float
    drift_ratio: float
    data_quality: float
    prediction_latency: float
    error_rate: float
    overall_health: str  # HEALTHY, DEGRADED, CRITICAL
    issues: List[str]

class HealthMonitor:
    """
    Continuous health monitoring for ML pipeline
    
    Monitors:
    - Model performance degradation
    - Data quality issues
    - Drift patterns
    - System performance
    """
    
    def __init__(self):
        self.health_history = []
        self.thresholds = {
            'accuracy_drop': 0.05,  # 5% drop triggers warning
            'drift_moderate': 0.25,
            'drift_severe': 0.50,
            'data_quality_min': 0.80,
            'error_rate_max': 0.10
        }
        print("[HealthMonitor] Initialized")
    
    def check_health(
        self,
        model_accuracy: float,
        baseline_accuracy: float,
        drift_ratio: float,
        data_quality: float,
        error_rate: float = 0.0,
        prediction_latency: float = 0.0
    ) -> HealthMetrics:
        """
        Comprehensive health check
        
        Returns:
            HealthMetrics with overall health status
        """
        issues = []
        
        # Check model performance
        accuracy_drop = baseline_accuracy - model_accuracy
        if accuracy_drop > self.thresholds['accuracy_drop']:
            issues.append(f"Model accuracy dropped {accuracy_drop:.1%}")
        
        # Check drift
        if drift_ratio > self.thresholds['drift_severe']:
            issues.append(f"SEVERE drift detected ({drift_ratio:.1%})")
        elif drift_ratio > self.thresholds['drift_moderate']:
            issues.append(f"MODERATE drift detected ({drift_ratio:.1%})")
        
        # Check data quality
        if data_quality < self.thresholds['data_quality_min']:
            issues.append(f"Low data quality ({data_quality:.1%})")
        
        # Check error rate
        if error_rate > self.thresholds['error_rate_max']:
            issues.append(f"High error rate ({error_rate:.1%})")
        
        # Determine overall health
        if len(issues) == 0:
            overall_health = "HEALTHY"
        elif len(issues) <= 2 and drift_ratio < self.thresholds['drift_severe']:
            overall_health = "DEGRADED"
        else:
            overall_health = "CRITICAL"
        
        metrics = HealthMetrics(
            timestamp=datetime.now().isoformat(),
            model_accuracy=model_accuracy,
            drift_ratio=drift_ratio,
            data_quality=data_quality,
            prediction_latency=prediction_latency,
            error_rate=error_rate,
            overall_health=overall_health,
            issues=issues
        )
        
        self.health_history.append(metrics)
        
        return metrics
    
    def get_health_trend(self, window: int = 10) -> str:
        """
        Analyze health trend over recent checks
        
        Returns:
            'improving', 'stable', 'degrading'
        """
        if len(self.health_history) < 2:
            return 'stable'
        
        recent = self.health_history[-window:]
        
        # Count health states
        healthy_count = sum(1 for h in recent if h.overall_health == "HEALTHY")
        critical_count = sum(1 for h in recent if h.overall_health == "CRITICAL")
        
        # Analyze trend
        if len(recent) >= 2:
            recent_healthy = sum(1 for h in recent[-3:] if h.overall_health == "HEALTHY")
            older_healthy = sum(1 for h in recent[:3] if h.overall_health == "HEALTHY")
            
            if recent_healthy > older_healthy:
                return 'improving'
            elif recent_healthy < older_healthy:
                return 'degrading'
        
        return 'stable'
    
    def get_summary(self) -> Dict:
        """Get health summary"""
        if not self.health_history:
            return {"status": "No data"}
        
        latest = self.health_history[-1]
        trend = self.get_health_trend()
        
        return {
            "current_health": latest.overall_health,
            "trend": trend,
            "model_accuracy": latest.model_accuracy,
            "drift_ratio": latest.drift_ratio,
            "data_quality": latest.data_quality,
            "issues": latest.issues,
            "checks_performed": len(self.health_history)
        }


# Test
if __name__ == "__main__":
    monitor = HealthMonitor()
    
    # Simulate health checks
    print("\n=== Health Monitoring Test ===\n")
    
    # Healthy state
    metrics1 = monitor.check_health(
        model_accuracy=0.95,
        baseline_accuracy=0.95,
        drift_ratio=0.10,
        data_quality=0.90
    )
    print(f"Check 1: {metrics1.overall_health}")
    print(f"  Issues: {metrics1.issues if metrics1.issues else 'None'}")
    
    # Degraded state
    metrics2 = monitor.check_health(
        model_accuracy=0.92,
        baseline_accuracy=0.95,
        drift_ratio=0.30,
        data_quality=0.85
    )
    print(f"\nCheck 2: {metrics2.overall_health}")
    print(f"  Issues: {metrics2.issues}")
    
    # Critical state
    metrics3 = monitor.check_health(
        model_accuracy=0.88,
        baseline_accuracy=0.95,
        drift_ratio=0.55,
        data_quality=0.75
    )
    print(f"\nCheck 3: {metrics3.overall_health}")
    print(f"  Issues: {metrics3.issues}")
    
    # Summary
    print(f"\n=== Summary ===")
    summary = monitor.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
