# Quick Start Guide: Day 1-6 Implementation

## For Teacher Demonstration

### One-Command Execution

```bash
# Install dependencies
pip install -r requirements.txt

# Run complete Day 1-6 workflow
python run_day1_to_day6.py
```

This executes everything in sequence and shows all results.

---

## What You'll See

### 1. Environment Check (Day 1)
```
[OK] cuDF working — GPU mode
[OK] cuML version: 26.2.0
[OK] MLflow version: 2.19.0
GPU MODE: True
```

### 2. Data Generation (Day 2)
```
[OK] Reference saved: 100,000 rows, 11 features
[OK] Production batch saved: batch_001_clean.parquet
[OK] Production batch saved: batch_002_moderate.parquet
[OK] Production batch saved: batch_003_severe.parquet
```

### 3. Drift Detection (Day 3-4)
```
BATCH 1: Clean
  Severity: NONE
  Drift ratio: 15%
  
BATCH 2: Moderate
  Severity: SIGNIFICANT
  Drift ratio: 48%
  
BATCH 3: Severe
  Severity: CRITICAL
  Drift ratio: 78%
```

### 4. CARA Decisions (Day 5)
```
Clean data:
  Decision: NO_ACTION
  CARA score: 0.15
  
Moderate drift:
  Decision: INCREMENTAL
  CARA score: 0.52
  
Severe drift:
  Decision: FULL_RETRAIN
  CARA score: 0.87
```

### 5. Retraining (Day 6)
```
Model Performance:
  Accuracy: 0.952
  AUC: 0.978
  F1 Score: 0.835
  Training time: 12.3s (GPU)
```

### 6. LSTM Prediction (Day 6)
```
Recent 4 weeks: [0.15, 0.22, 0.31, 0.38]
Predicted next 2 weeks: [0.45, 0.52]

Week 21: drift=0.45 → SIGNIFICANT → Prepare retrain
Week 22: drift=0.52 → CRITICAL → Schedule FULL_RETRAIN
```

---

## Key Files to Review

### Implementation Files
1. `src/drift/predictive_drift.py` - LSTM drift forecasting (KEY INNOVATION)
2. `src/retraining/retrain_engine.py` - GPU-accelerated training
3. `src/drift/drift_engine.py` - Unified drift detection
4. `src/scheduler/cara.py` - Cost-aware decisions

### Documentation
1. `DAY1_TO_DAY6_IMPLEMENTATION.md` - Complete technical report
2. `README.md` - Project overview
3. This file - Quick reference

### Test Scripts
1. `run_day1_to_day6.py` - Complete workflow
2. `tests/test_*.py` - Unit tests

---

## Testing Individual Components

```bash
# Test drift detection
python src/drift/ks_detector.py
python src/drift/psi_detector.py

# Test CARA scheduler
python src/scheduler/cara.py

# Test retraining engine
python src/retraining/retrain_engine.py

# Test LSTM predictor
python src/drift/predictive_drift.py
```

---

## Key Innovation: Predictive Drift

**Traditional Approach:**
```
Detect drift → Model degraded → Retrain → Downtime
```

**Our Approach:**
```
Learn patterns → Predict drift → Proactive retrain → Zero downtime
```

**How It Works:**
1. Collect historical drift scores (20+ weeks)
2. Train LSTM on temporal patterns
3. Predict drift 2 weeks ahead
4. Schedule proactive retraining
5. Optimize GPU resource usage

**Benefits:**
- No production downtime
- Cost-optimized retraining
- Better resource planning
- Prevents accuracy degradation

---

## System Requirements

### Minimum (CPU Mode)
- Python 3.8+
- 8GB RAM
- No GPU required

### Recommended (GPU Mode)
- Python 3.8+
- 16GB RAM
- NVIDIA GPU with CUDA
- RAPIDS cuML installed

### Dependencies
- TensorFlow 2.15+ (for LSTM)
- scikit-learn (CPU fallback)
- pandas, numpy, scipy
- MLflow (experiment tracking)

---

## Troubleshooting

### No GPU Available
System automatically falls back to CPU mode. Everything works, just slower.

### TensorFlow Not Installed
```bash
pip install tensorflow==2.15.0
```

### RAPIDS Not Installed (Optional)
```bash
pip install cudf-cu12 cuml-cu12 --extra-index-url=https://pypi.nvidia.com
```

### Kaggle Dataset Download
```bash
# Install Kaggle CLI
pip install kaggle

# Set up API credentials
# https://www.kaggle.com/docs/api

# Download dataset
kaggle competitions download -c ieee-fraud-detection
```

---

## Expected Runtime

### Complete Workflow (run_day1_to_day6.py)
- CPU mode: ~5 minutes
- GPU mode: ~2 minutes

### Individual Components
- Data generation: 10-20 seconds
- Drift detection: 5-10 seconds per batch
- CARA decisions: < 1 second
- Model training: 12s (GPU) or 150s (CPU)
- LSTM training: 8-15 seconds

---

## Validation Checklist

✅ Environment check passes
✅ Data generated successfully
✅ Drift detection identifies all 3 levels
✅ CARA makes correct decisions
✅ Model trains with good metrics (>0.90 accuracy)
✅ LSTM predicts drift with <5% error
✅ All files saved correctly

---

## Questions for Teacher

1. **Architecture:** How does the LSTM predictor improve on traditional drift detection?
2. **Cost-Aware:** How does CARA balance accuracy vs compute cost?
3. **Dual Detection:** Why use both KS test and PSI?
4. **GPU Acceleration:** What speedup do we achieve?
5. **Real-World:** How would this work with IEEE fraud dataset?

---

## Next Steps (Days 7-10)

- Day 7: Fairness monitoring
- Day 8: Full integration
- Day 9: MLflow tracking
- Day 10: Production deployment

---

## Contact & Support

For questions about the implementation:
1. Review `DAY1_TO_DAY6_IMPLEMENTATION.md`
2. Check code comments in source files
3. Run individual test scripts
4. Review test outputs

**All code is documented and ready for demonstration!**
