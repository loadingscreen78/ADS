# Quick Start Guide - Day 1 to Day 5

This guide walks you through executing Day 1 to Day 5 tasks of the ML Auto-Retrain system.

## Prerequisites

- Python 3.11+
- pip package manager
- (Optional) NVIDIA GPU with CUDA support for GPU acceleration
- (Optional) Docker Desktop for containerized services

## Installation

### 1. Install Dependencies

```bash
# Install core dependencies (CPU mode)
pip install -r requirements.txt
```

For GPU support (optional):
```bash
# Install RAPIDS cuDF and cuML
pip install cudf-cu12==26.2.0 cuml-cu12==26.2.0 \
    --extra-index-url=https://pypi.nvidia.com
```

### 2. Verify Environment

```bash
python check_env.py
```

Expected output:
```
==================================================
ENVIRONMENT CHECK
==================================================
[WARN] cuDF not found — falling back to CPU pandas
[OK] MLflow version: 2.19.0
[OK] scipy available — KS test ready
==================================================
GPU MODE: False
==================================================
```

## Running Day 1-5 Tasks

### Option 1: Automated Workflow (Recommended)

Run all Day 1-5 tasks automatically:

```bash
python run_day1_to_day5.py
```

This script will:
1. Check environment (Day 1)
2. Generate synthetic data (Day 2)
3. Test drift detection modules (Day 3-4)
4. Test CARA scheduler (Day 5)
5. Run all unit tests

### Option 2: Manual Step-by-Step

#### Day 1: Environment Setup
```bash
python check_env.py
```

#### Day 2: Generate Synthetic Data
```bash
python src/utils/data_generator.py
```

Verify data files created:
- `data/reference/reference.parquet` (100K rows)
- `data/production/batch_001_clean.parquet` (50K rows, no drift)
- `data/production/batch_002_moderate.parquet` (50K rows, moderate drift)
- `data/production/batch_003_severe.parquet` (50K rows, severe drift)

#### Day 3-4: Test Drift Detection

Test KS Detector:
```bash
python src/drift/ks_detector.py
```

Test PSI Detector:
```bash
python src/drift/psi_detector.py
```

Test Unified Drift Engine:
```bash
python src/drift/drift_engine.py
```

#### Day 5: Test CARA Scheduler
```bash
python src/scheduler/cara.py
```

#### Run Unit Tests
```bash
python tests/test_ks.py
python tests/test_psi.py
python tests/test_cara.py
```

## Understanding the Output

### KS Drift Report
```
==================================================
KS DRIFT REPORT
==================================================
Feature                      Stat   p-val  Drifted  Severity
--------------------------------------------------
amount                     0.1234  0.0001   YES ⚠    severe
is_international           0.0856  0.0023   YES ⚠  moderate
...
```

- **Stat**: KS statistic (0-1, higher = more drift)
- **p-val**: p-value (< 0.05 = statistically significant drift)
- **Drifted**: YES if p-value < 0.05
- **Severity**: none, low, moderate, severe

### PSI Drift Report
```
======================================================================
PSI DRIFT REPORT
======================================================================
Feature                      PSI    Severity  Drifted  Mean Shift
----------------------------------------------------------------------
amount                    0.4523  significant   YES ⚠      +42.3%
is_international          0.3214  significant   YES ⚠      +125.0%
...
```

- **PSI**: Population Stability Index
  - < 0.10: No significant shift
  - 0.10-0.25: Moderate shift
  - > 0.25: Significant shift (action required)
- **Mean Shift**: Percentage change in feature mean

### CARA Decision
```
============================================================
CARA DECISION
============================================================
Decision:      FULL_RETRAIN
CARA Score:    0.7845
Expected Gain: 5.60%
Compute Cost:  0.0500
Data Quality:  0.85
Timestamp:     2026-04-06T13:36:42.123456

Justification:
  CARA score 0.785 ≥ 0.7. Drift severity: SIGNIFICANT.
  Expected gain: 5.60%. Drifted features: ['amount', 
  'is_international', 'merchant_category']. 
  Full retrain justified.
============================================================
```

## Project Structure

```
ml-autoretrain/
├── check_env.py              # Environment verification
├── run_day1_to_day5.py       # Automated workflow script
├── requirements.txt          # Python dependencies
├── docker-compose.yml        # Docker services configuration
│
├── data/
│   ├── reference/            # Training distribution baseline
│   ├── production/           # Production batches (simulated)
│   └── models/               # Saved model artifacts
│
├── src/
│   ├── drift/
│   │   ├── ks_detector.py    # Kolmogorov-Smirnov test
│   │   ├── psi_detector.py   # Population Stability Index
│   │   └── drift_engine.py   # Unified drift detection
│   │
│   ├── scheduler/
│   │   └── cara.py           # Cost-Aware Retraining Algorithm
│   │
│   └── utils/
│       └── data_generator.py # Synthetic data generation
│
└── tests/
    ├── test_ks.py            # KS detector tests
    ├── test_psi.py           # PSI detector tests
    └── test_cara.py          # CARA scheduler tests
```

## Troubleshooting

### Import Errors
If you see `ModuleNotFoundError`:
```bash
# Make sure you're in the project root directory
cd ml-autoretrain

# Install dependencies
pip install -r requirements.txt
```

### Data Files Not Found
If tests fail with "file not found":
```bash
# Generate data first
python src/utils/data_generator.py
```

### GPU Not Detected
This is normal if you don't have an NVIDIA GPU. The system automatically falls back to CPU mode using pandas and scikit-learn.

## Next Steps

After completing Day 1-5:

1. **Day 6-7**: Implement cuML Retraining Engine
2. **Day 8**: Wire CARA with Retraining
3. **Day 9**: MLflow Integration
4. **Day 10**: Docker Services & End-to-End Testing

## Docker Services (Day 5+)

Start all services:
```bash
docker-compose up -d
```

Access services:
- MLflow UI: http://localhost:5000
- Drift Monitor API: http://localhost:8001
- Retrain Engine API: http://localhost:8002

Stop services:
```bash
docker-compose down
```

## Support

For issues or questions:
1. Check the main implementation guide: `ML_AutoRetrain_Implementation_Guide.md`
2. Review test outputs for specific error messages
3. Verify all dependencies are installed correctly
