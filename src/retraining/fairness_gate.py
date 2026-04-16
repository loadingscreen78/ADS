"""
Fairness Monitoring Module
Day 7 Implementation

Monitors model fairness across demographic groups and ensures
equitable predictions for all protected classes.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import matplotlib.pyplot as plt
import seaborn as sns


@dataclass
class FairnessMetrics:
    """Container for fairness metrics."""
    demographic_parity: float
    equal_opportunity: float
    equalized_odds: float
    disparate_impact: float
    group_sizes: Dict[str, int]
    group_positive_rates: Dict[str, float]
    is_fair: bool
    violations: List[str]


class FairnessMonitor:
    """
    Fairness monitoring for fraud detection models.
    
    Monitors:
    - Demographic Parity: Equal positive prediction rates across groups
    - Equal Opportunity: Equal true positive rates across groups
    - Equalized Odds: Equal TPR and FPR across groups
    - Disparate Impact: Ratio of positive rates (should be > 0.8)
    
    Protected attributes (simulated):
    - Age group (young, middle, senior)
    - Transaction location (domestic, international)
    - Merchant category
    """
    
    # Fairness thresholds
    DEMOGRAPHIC_PARITY_THRESHOLD = 0.1  # Max difference in positive rates
    EQUAL_OPPORTUNITY_THRESHOLD = 0.1   # Max difference in TPR
    DISPARATE_IMPACT_THRESHOLD = 0.8     # Min ratio (80% rule)
    
    def __init__(self, protected_attributes: List[str] = None):
        """
        Initialize fairness monitor.
        
        Args:
            protected_attributes: List of features to monitor for fairness
        """
        self.protected_attributes = protected_attributes or [
            'user_age_bucket',
            'is_international',
            'merchant_category'
        ]
        self.fairness_history = []
        
    def _create_groups(self, df: pd.DataFrame, attribute: str) -> Dict[str, pd.DataFrame]:
        """Create groups based on protected attribute."""
        groups = {}
        
        if attribute == 'user_age_bucket':
            # Age groups: 0-2 (young), 3-4 (middle), 5+ (senior)
            df_copy = df.copy()
            df_copy['age_group'] = pd.cut(
                df_copy[attribute], 
                bins=[-1, 2, 4, 10], 
                labels=['young', 'middle', 'senior']
            )
            for group in ['young', 'middle', 'senior']:
                groups[group] = df_copy[df_copy['age_group'] == group]
                
        elif attribute == 'is_international':
            groups['domestic'] = df[df[attribute] == 0]
            groups['international'] = df[df[attribute] == 1]
            
        elif attribute == 'merchant_category':
            # Group merchant categories
            for cat in df[attribute].unique():
                groups[f'cat_{int(cat)}'] = df[df[attribute] == cat]
        else:
            # Generic grouping
            for val in df[attribute].unique():
                groups[f'{attribute}_{val}'] = df[df[attribute] == val]
                
        return groups
    
    def compute_demographic_parity(
        self, 
        predictions: np.ndarray,
        groups: Dict[str, pd.DataFrame]
    ) -> Tuple[float, Dict[str, float]]:
        """
        Compute demographic parity difference.
        
        Demographic Parity: P(Ŷ=1|A=0) ≈ P(Ŷ=1|A=1)
        
        Returns:
            Tuple of (max_difference, group_positive_rates)
        """
        group_rates = {}
        
        for group_name, group_df in groups.items():
            if len(group_df) > 0:
                # Get predictions for this group
                group_preds = predictions[group_df.index]
                positive_rate = group_preds.mean()
                group_rates[group_name] = positive_rate
        
        if len(group_rates) < 2:
            return 0.0, group_rates
        
        max_diff = max(group_rates.values()) - min(group_rates.values())
        return max_diff, group_rates
    
    def compute_equal_opportunity(
        self,
        predictions: np.ndarray,
        labels: np.ndarray,
        groups: Dict[str, pd.DataFrame]
    ) -> float:
        """
        Compute equal opportunity difference.
        
        Equal Opportunity: P(Ŷ=1|Y=1,A=0) ≈ P(Ŷ=1|Y=1,A=1)
        True Positive Rate should be equal across groups.
        
        Returns:
            Max difference in TPR across groups
        """
        group_tprs = {}
        
        for group_name, group_df in groups.items():
            # Get positive samples in this group
            positive_mask = labels[group_df.index] == 1
            if positive_mask.sum() > 0:
                # TPR = TP / (TP + FN) = P(Ŷ=1|Y=1)
                group_preds = predictions[group_df.index][positive_mask]
                tpr = group_preds.mean()
                group_tprs[group_name] = tpr
        
        if len(group_tprs) < 2:
            return 0.0
        
        max_diff = max(group_tprs.values()) - min(group_tprs.values())
        return max_diff
    
    def compute_disparate_impact(
        self,
        predictions: np.ndarray,
        groups: Dict[str, pd.DataFrame]
    ) -> float:
        """
        Compute disparate impact ratio.
        
        Disparate Impact: min(P(Ŷ=1|A)) / max(P(Ŷ=1|A)) >= 0.8
        
        Returns:
            Ratio of minimum to maximum positive rate
        """
        group_rates = {}
        
        for group_name, group_df in groups.items():
            if len(group_df) > 0:
                group_preds = predictions[group_df.index]
                group_rates[group_name] = group_preds.mean()
        
        if len(group_rates) < 2:
            return 1.0
        
        min_rate = min(group_rates.values())
        max_rate = max(group_rates.values())
        
        if max_rate == 0:
            return 1.0
        
        return min_rate / max_rate
    
    def evaluate_fairness(
        self,
        df: pd.DataFrame,
        predictions: np.ndarray,
        labels: np.ndarray,
        attribute: str
    ) -> FairnessMetrics:
        """
        Evaluate fairness for a specific protected attribute.
        
        Args:
            df: DataFrame with features
            predictions: Model predictions (binary)
            labels: True labels
            attribute: Protected attribute to evaluate
            
        Returns:
            FairnessMetrics object
        """
        # Create groups
        groups = self._create_groups(df, attribute)
        
        # Compute metrics
        dp_diff, group_rates = self.compute_demographic_parity(predictions, groups)
        eo_diff = self.compute_equal_opportunity(predictions, labels, groups)
        di_ratio = self.compute_disparate_impact(predictions, groups)
        
        # Check violations
        violations = []
        is_fair = True
        
        if dp_diff > self.DEMOGRAPHIC_PARITY_THRESHOLD:
            violations.append(
                f"Demographic parity violation: {dp_diff:.3f} > {self.DEMOGRAPHIC_PARITY_THRESHOLD}"
            )
            is_fair = False
        
        if eo_diff > self.EQUAL_OPPORTUNITY_THRESHOLD:
            violations.append(
                f"Equal opportunity violation: {eo_diff:.3f} > {self.EQUAL_OPPORTUNITY_THRESHOLD}"
            )
            is_fair = False
        
        if di_ratio < self.DISPARATE_IMPACT_THRESHOLD:
            violations.append(
                f"Disparate impact violation: {di_ratio:.3f} < {self.DISPARATE_IMPACT_THRESHOLD}"
            )
            is_fair = False
        
        # Group sizes
        group_sizes = {name: len(g) for name, g in groups.items()}
        
        return FairnessMetrics(
            demographic_parity=dp_diff,
            equal_opportunity=eo_diff,
            equalized_odds=eo_diff,  # Simplified
            disparate_impact=di_ratio,
            group_sizes=group_sizes,
            group_positive_rates=group_rates,
            is_fair=is_fair,
            violations=violations
        )
    
    def monitor_all_attributes(
        self,
        df: pd.DataFrame,
        predictions: np.ndarray,
        labels: np.ndarray
    ) -> Dict[str, FairnessMetrics]:
        """
        Monitor fairness across all protected attributes.
        
        Returns:
            Dictionary mapping attribute name to FairnessMetrics
        """
        results = {}
        
        for attribute in self.protected_attributes:
            if attribute in df.columns:
                metrics = self.evaluate_fairness(df, predictions, labels, attribute)
                results[attribute] = metrics
                
                # Log results
                status = "✓ FAIR" if metrics.is_fair else "✗ UNFAIR"
                print(f"[Fairness] {attribute}: {status}")
                if not metrics.is_fair:
                    for violation in metrics.violations:
                        print(f"  - {violation}")
        
        # Store in history
        self.fairness_history.append(results)
        
        return results
    
    def generate_fairness_report(
        self,
        results: Dict[str, FairnessMetrics],
        save_path: str = None
    ) -> str:
        """
        Generate a comprehensive fairness report.
        
        Args:
            results: Fairness evaluation results
            save_path: Path to save the report
            
        Returns:
            Report as string
        """
        report = []
        report.append("=" * 70)
        report.append("FAIRNESS MONITORING REPORT")
        report.append("=" * 70)
        report.append("")
        
        overall_fair = True
        
        for attribute, metrics in results.items():
            report.append(f"\nProtected Attribute: {attribute}")
            report.append("-" * 70)
            report.append(f"  Demographic Parity Diff: {metrics.demographic_parity:.4f}")
            report.append(f"  Equal Opportunity Diff:  {metrics.equal_opportunity:.4f}")
            report.append(f"  Disparate Impact Ratio:  {metrics.disparate_impact:.4f}")
            report.append(f"  Status: {'✓ FAIR' if metrics.is_fair else '✗ UNFAIR'}")
            
            report.append(f"\n  Group Statistics:")
            for group, size in metrics.group_sizes.items():
                rate = metrics.group_positive_rates.get(group, 0)
                report.append(f"    {group}: {size:,} samples, positive rate: {rate:.2%}")
            
            if not metrics.is_fair:
                overall_fair = False
                report.append(f"\n  Violations:")
                for violation in metrics.violations:
                    report.append(f"    - {violation}")
        
        report.append("\n" + "=" * 70)
        report.append(f"OVERALL STATUS: {'✓ FAIR' if overall_fair else '✗ UNFAIR'}")
        report.append("=" * 70)
        
        report_text = "\n".join(report)
        
        if save_path:
            with open(save_path, 'w') as f:
                f.write(report_text)
            print(f"[Fairness] Report saved to {save_path}")
        
        return report_text
    
    def plot_fairness_metrics(
        self,
        results: Dict[str, FairnessMetrics],
        save_path: str = None
    ):
        """
        Plot fairness metrics visualization.
        
        Args:
            results: Fairness evaluation results
            save_path: Path to save the plot
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Fairness Monitoring Dashboard', fontsize=16, fontweight='bold')
        
        # Plot 1: Demographic Parity
        ax1 = axes[0, 0]
        attributes = list(results.keys())
        dp_values = [results[a].demographic_parity for a in attributes]
        colors = ['green' if v <= self.DEMOGRAPHIC_PARITY_THRESHOLD else 'red' for v in dp_values]
        ax1.bar(range(len(attributes)), dp_values, color=colors)
        ax1.axhline(y=self.DEMOGRAPHIC_PARITY_THRESHOLD, color='red', linestyle='--', label='Threshold')
        ax1.set_xticks(range(len(attributes)))
        ax1.set_xticklabels(attributes, rotation=45, ha='right')
        ax1.set_ylabel('Demographic Parity Difference')
        ax1.set_title('Demographic Parity')
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)
        
        # Plot 2: Equal Opportunity
        ax2 = axes[0, 1]
        eo_values = [results[a].equal_opportunity for a in attributes]
        colors = ['green' if v <= self.EQUAL_OPPORTUNITY_THRESHOLD else 'red' for v in eo_values]
        ax2.bar(range(len(attributes)), eo_values, color=colors)
        ax2.axhline(y=self.EQUAL_OPPORTUNITY_THRESHOLD, color='red', linestyle='--', label='Threshold')
        ax2.set_xticks(range(len(attributes)))
        ax2.set_xticklabels(attributes, rotation=45, ha='right')
        ax2.set_ylabel('Equal Opportunity Difference')
        ax2.set_title('Equal Opportunity')
        ax2.legend()
        ax2.grid(axis='y', alpha=0.3)
        
        # Plot 3: Disparate Impact
        ax3 = axes[1, 0]
        di_values = [results[a].disparate_impact for a in attributes]
        colors = ['green' if v >= self.DISPARATE_IMPACT_THRESHOLD else 'red' for v in di_values]
        ax3.bar(range(len(attributes)), di_values, color=colors)
        ax3.axhline(y=self.DISPARATE_IMPACT_THRESHOLD, color='red', linestyle='--', label='Threshold (0.8)')
        ax3.set_xticks(range(len(attributes)))
        ax3.set_xticklabels(attributes, rotation=45, ha='right')
        ax3.set_ylabel('Disparate Impact Ratio')
        ax3.set_title('Disparate Impact')
        ax3.legend()
        ax3.grid(axis='y', alpha=0.3)
        
        # Plot 4: Group Sizes
        ax4 = axes[1, 1]
        for i, (attr, metrics) in enumerate(results.items()):
            groups = list(metrics.group_sizes.keys())
            sizes = list(metrics.group_sizes.values())
            ax4.bar(range(len(groups)), sizes, alpha=0.7, label=attr)
        ax4.set_ylabel('Group Size')
        ax4.set_title('Group Sizes by Protected Attribute')
        ax4.legend()
        ax4.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"[Fairness] Plot saved to {save_path}")
        
        plt.close()


# ── TEST ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n=== Testing Fairness Monitor ===\n")
    
    # Create test data
    np.random.seed(42)
    n_samples = 1000
    
    test_df = pd.DataFrame({
        'user_age_bucket': np.random.randint(0, 6, n_samples),
        'is_international': np.random.binomial(1, 0.1, n_samples),
        'merchant_category': np.random.randint(0, 5, n_samples)
    })
    
    # Simulate predictions (with some bias)
    predictions = np.random.binomial(1, 0.05, n_samples)
    labels = np.random.binomial(1, 0.05, n_samples)
    
    # Initialize monitor
    monitor = FairnessMonitor()
    
    # Evaluate fairness
    results = monitor.monitor_all_attributes(test_df, predictions, labels)
    
    # Generate report
    report = monitor.generate_fairness_report(results, "data/models/fairness_report.txt")
    print(report)
    
    # Generate plots
    monitor.plot_fairness_metrics(results, "data/models/fairness_dashboard.png")
    
    print("\n[OK] Fairness monitoring test complete!")