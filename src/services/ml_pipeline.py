"""
Complete ML Pipeline Integration
Day 8 Implementation

Integrates all components into a unified pipeline:
- Drift Detection
- CARA Scheduler
- Retraining Engine
- Fairness Monitoring
- Audit Logging
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import all components
from src.drift.drift_engine import DriftEngine, DriftScore
from src.scheduler.cara import CARAScheduler, CARAOutput
from src.retraining.retrain_engine import RetrainEngine, ModelMetrics
from src.retraining.fairness_gate import FairnessMonitor, FairnessMetrics


class AuditLogger:
    """Audit logging for all pipeline actions."""
    
    def __init__(self, log_path: str = "data/audit_log.json"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.logs = []
        
    def log(self, action: str, details: Dict[str, Any]):
        """Log an action with details."""
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'details': details
        }
        self.logs.append(entry)
        
        # Append to file
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def get_recent_logs(self, n: int = 10) -> list:
        """Get n most recent logs."""
        return self.logs[-n:]


class MLPipeline:
    """
    Complete ML Pipeline for Auto-Retraining.
    
    Integrates:
    1. Drift Detection (KS + PSI)
    2. CARA Scheduler (Cost-aware decisions)
    3. Retraining Engine (GPU/CPU)
    4. Fairness Monitoring (Demographic parity, etc.)
    5. Audit Logging (Full traceability)
    
    Workflow:
    1. Load production batch
    2. Detect drift
    3. Check fairness
    4. Make CARA decision
    5. Execute retrain if needed
    6. Log everything
    """
    
    def __init__(
        self,
        reference_path: str = "data/reference/reference.parquet",
        model_dir: str = "data/models",
        use_gpu: bool = False
    ):
        """Initialize complete pipeline."""
        print("=" * 70)
        print("INITIALIZING ML PIPELINE")
        print("=" * 70)
        
        # Initialize components
        self.drift_engine = DriftEngine(reference_path)
        self.cara_scheduler = CARAScheduler()
        self.retrain_engine = RetrainEngine(model_dir, use_gpu=use_gpu)
        self.fairness_monitor = FairnessMonitor()
        self.audit_logger = AuditLogger()
        
        # State
        self.current_model_version = 0
        self.baseline_accuracy = 0.95
        self.current_accuracy = 0.95
        self.processed_batches = 0
        
        print(f"[Pipeline] Initialized successfully")
        print(f"  - Drift Engine: ✓")
        print(f"  - CARA Scheduler: ✓")
        print(f"  - Retrain Engine: ✓")
        print(f"  - Fairness Monitor: ✓")
        print(f"  - Audit Logger: ✓")
        print("=" * 70)
    
    def process_batch(
        self,
        batch_path: str,
        batch_id: str,
        auto_retrain: bool = True
    ) -> Dict[str, Any]:
        """
        Process a production batch through the complete pipeline.
        
        Args:
            batch_path: Path to production batch
            batch_id: Unique batch identifier
            auto_retrain: Whether to automatically execute retrain decisions
            
        Returns:
            Dictionary with all results
        """
        print("\n" + "=" * 70)
        print(f"PROCESSING BATCH: {batch_id}")
        print("=" * 70)
        
        start_time = time.time()
        results = {
            'batch_id': batch_id,
            'timestamp': datetime.utcnow().isoformat(),
            'drift_score': None,
            'fairness_metrics': None,
            'cara_decision': None,
            'retrain_result': None,
            'status': 'processing'
        }
        
        # Log batch start
        self.audit_logger.log('batch_start', {'batch_id': batch_id, 'path': batch_path})
        
        # Step 1: Drift Detection
        print("\n[Step 1/4] Detecting drift...")
        drift_score = self.drift_engine.analyze_batch(batch_path, batch_id)
        results['drift_score'] = drift_score.to_dict()
        
        self.audit_logger.log('drift_detected', {
            'batch_id': batch_id,
            'drift_ratio': drift_score.drift_ratio,
            'severity': drift_score.overall_severity
        })
        
        # Step 2: Fairness Check
        print("\n[Step 2/4] Checking fairness...")
        try:
            batch_df = pd.read_parquet(batch_path)
            
            # Get predictions from current model
            if self.retrain_engine.current_model is not None:
                predictions = self.retrain_engine.predict(batch_df)
                labels = batch_df['is_fraud'].values if 'is_fraud' in batch_df.columns else np.zeros(len(batch_df))
                
                fairness_results = self.fairness_monitor.monitor_all_attributes(
                    batch_df, predictions, labels
                )
                results['fairness_metrics'] = {
                    attr: {
                        'is_fair': metrics.is_fair,
                        'demographic_parity': metrics.demographic_parity,
                        'disparate_impact': metrics.disparate_impact
                    }
                    for attr, metrics in fairness_results.items()
                }
                
                self.audit_logger.log('fairness_check', {
                    'batch_id': batch_id,
                    'overall_fair': all(m.is_fair for m in fairness_results.values())
                })
        except Exception as e:
            print(f"[WARN] Fairness check failed: {e}")
            results['fairness_metrics'] = {'error': str(e)}
        
        # Step 3: CARA Decision
        print("\n[Step 3/4] Making CARA decision...")
        cara_decision = self.cara_scheduler.decide(
            drift_score=drift_score,
            current_acc=self.current_accuracy,
            baseline_acc=self.baseline_accuracy
        )
        results['cara_decision'] = {
            'decision': cara_decision.decision.value,
            'score': cara_decision.score,
            'expected_gain': cara_decision.expected_gain,
            'justification': cara_decision.justification
        }
        
        self.audit_logger.log('cara_decision', {
            'batch_id': batch_id,
            'decision': cara_decision.decision.value,
            'score': cara_decision.score
        })
        
        # Step 4: Execute Decision
        print("\n[Step 4/4] Executing decision...")
        if auto_retrain and cara_decision.decision.value in ['FULL_RETRAIN', 'INCREMENTAL']:
            print(f"[Pipeline] Executing {cara_decision.decision.value}...")
            
            if cara_decision.decision.value == 'FULL_RETRAIN':
                retrain_result = self.retrain_engine.train_full(batch_path)
            else:
                retrain_result = self.retrain_engine.train_incremental(batch_path)
            
            results['retrain_result'] = retrain_result.to_dict()
            self.current_model_version = self.retrain_engine.model_version
            self.current_accuracy = retrain_result.accuracy
            
            self.audit_logger.log('retrain_executed', {
                'batch_id': batch_id,
                'type': cara_decision.decision.value,
                'new_accuracy': retrain_result.accuracy,
                'model_version': self.current_model_version
            })
        else:
            print(f"[Pipeline] Decision: {cara_decision.decision.value} - No retrain needed")
        
        # Finalize
        elapsed = time.time() - start_time
        results['processing_time'] = elapsed
        results['status'] = 'completed'
        
        self.processed_batches += 1
        
        self.audit_logger.log('batch_complete', {
            'batch_id': batch_id,
            'processing_time': elapsed,
            'status': 'completed'
        })
        
        print("\n" + "=" * 70)
        print(f"BATCH PROCESSING COMPLETE")
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Drift: {drift_score.overall_severity} ({drift_score.drift_ratio:.1%})")
        print(f"  Decision: {cara_decision.decision.value}")
        print("=" * 70)
        
        return results
    
    def run_continuous_monitoring(
        self,
        batch_dir: str = "data/production",
        interval_seconds: int = 60
    ):
        """
        Run continuous monitoring on production batches.
        
        Args:
            batch_dir: Directory containing production batches
            interval_seconds: Time between checks
        """
        print("\n" + "=" * 70)
        print("STARTING CONTINUOUS MONITORING")
        print("=" * 70)
        
        batch_dir = Path(batch_dir)
        processed_files = set()
        
        while True:
            try:
                # Find new batches
                batch_files = sorted(batch_dir.glob("batch_*.parquet"))
                new_batches = [f for f in batch_files if str(f) not in processed_files]
                
                if new_batches:
                    print(f"\n[Monitor] Found {len(new_batches)} new batch(es)")
                    
                    for batch_file in new_batches:
                        batch_id = batch_file.stem.replace('batch_', '')
                        self.process_batch(str(batch_file), batch_id)
                        processed_files.add(str(batch_file))
                else:
                    print(f"[Monitor] No new batches. Waiting {interval_seconds}s...")
                
                time.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                print("\n[Monitor] Stopping continuous monitoring")
                break
            except Exception as e:
                print(f"[ERROR] Monitoring error: {e}")
                time.sleep(interval_seconds)
    
    def generate_pipeline_report(self) -> str:
        """Generate comprehensive pipeline status report."""
        report = []
        report.append("=" * 70)
        report.append("ML PIPELINE STATUS REPORT")
        report.append("=" * 70)
        report.append(f"\nTimestamp: {datetime.utcnow().isoformat()}")
        report.append(f"Processed Batches: {self.processed_batches}")
        report.append(f"Current Model Version: {self.current_model_version}")
        report.append(f"Baseline Accuracy: {self.baseline_accuracy:.2%}")
        report.append(f"Current Accuracy: {self.current_accuracy:.2%}")
        
        report.append("\n" + "-" * 70)
        report.append("COMPONENT STATUS")
        report.append("-" * 70)
        report.append(f"  Drift Engine: ✓ Active")
        report.append(f"  CARA Scheduler: ✓ Active")
        report.append(f"  Retrain Engine: ✓ Active")
        report.append(f"  Fairness Monitor: ✓ Active")
        report.append(f"  Audit Logger: ✓ Active ({len(self.audit_logger.logs)} entries)")
        
        report.append("\n" + "-" * 70)
        report.append("RECENT ACTIONS")
        report.append("-" * 70)
        for log in self.audit_logger.get_recent_logs(5):
            report.append(f"  [{log['timestamp']}] {log['action']}")
        
        report.append("\n" + "=" * 70)
        
        return "\n".join(report)


# ── TEST ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n=== Testing Complete ML Pipeline ===\n")
    
    # Initialize pipeline
    pipeline = MLPipeline(
        reference_path="data/reference/reference.parquet",
        use_gpu=False
    )
    
    # Process all production batches
    batches = [
        ("data/production/batch_001_clean.parquet", "001_clean"),
        ("data/production/batch_002_moderate.parquet", "002_moderate"),
        ("data/production/batch_003_severe.parquet", "003_severe")
    ]
    
    all_results = []
    for batch_path, batch_id in batches:
        result = pipeline.process_batch(batch_path, batch_id, auto_retrain=True)
        all_results.append(result)
    
    # Generate report
    report = pipeline.generate_pipeline_report()
    print(report)
    
    # Save results
    with open("data/models/pipeline_results.json", 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print("\n[OK] Complete pipeline test successful!")