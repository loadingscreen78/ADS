"""
Self-Healing ML Pipeline
Based on: Self-Healing Machine Learning Pipelines (arXiv:2411.00186)

Components:
- Monitor: Continuous health monitoring
- Diagnosis: Root cause analysis
- Remediation: Automatic fixes
- Feedback: Self-improvement loop
"""

from .monitor import HealthMonitor
from .diagnosis import DiagnosisEngine
from .remediation import RemediationEngine

__all__ = ['HealthMonitor', 'DiagnosisEngine', 'RemediationEngine']
