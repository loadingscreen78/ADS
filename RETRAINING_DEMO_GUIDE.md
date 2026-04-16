# 🎯 RETRAINING DEMO GUIDE FOR JUDGES

## Overview
This guide shows how to demonstrate the complete ML Auto-Retrain system with **all retraining scenarios** including DEFER, RETRAIN_INCREMENTAL, and RETRAIN_FULL.

---

## 🚀 Quick Start

### Prerequisites
1. **Server Running**: API server at `http://localhost:8080`
2. **Dashboard Open**: Open `http://localhost:8080` in browser
3. **Files Ready**: All test batches are prepared

### Test Files Location
```
📁 Project Root
├── data/large_scale/
│   ├── original_100K.parquet      (100K rows, 6.04% fraud) - BASELINE
│   └── drifted_100K.parquet       (100K rows, 9.11% fraud) - MODERATE DRIFT
├── custom_uploads/
│   ├── custom_test_10K.parquet    (10K rows, moderate drift)
│   └── custom_test_10K.xlsx       (Excel for judges)
└── extreme_drift/
    ├── extreme_drift_50K.parquet  (50K rows, 21.14% fraud) - EXTREME DRIFT
    └── extreme_drift_50K.xlsx     (Excel for judges)
```

---

## 📊 TEST CASE 1: BASELINE (No Drift)
**Purpose**: Show system with clean data - no retraining needed

### Steps:
1. Open dashboard: `http://localhost:8080`
2. Click **"Upload Original Batch"** button (top left)
3. Wait for processing (~10-15 seconds)

### Expected Results:
```
✅ Batch ID: original_batch
✅ Rows: 100,000
✅ Fraud Rate: 6.04%
✅ Drift Ratio: 0-5% (MINIMAL)
✅ Severity: NONE or LOW
✅ CARA Score: < 0.3
✅ CARA Decision: DEFER
✅ Action: No retraining needed
```

### What to Show Judges:
- **Drift Detection Tab**: Green status, low drift ratio
- **CARA Analysis Tab**: DEFER decision with explanation
- **Drift History Chart**: First data point added
- **Audit Log**: Shows batch upload and analysis

---

## 📊 TEST CASE 2: MODERATE DRIFT (Incremental Retrain)
**Purpose**: Show incremental retraining for moderate drift

### Steps:
1. Click **"Upload Drifted Batch"** button (top right)
2. Wait for processing (~10-15 seconds)

### Expected Results:
```
✅ Batch ID: drifted_batch
✅ Rows: 100,000
✅ Fraud Rate: 9.11% (+51% vs baseline)
✅ Drift Ratio: 15-30% (MODERATE)
✅ Severity: MODERATE
✅ CARA Score: 0.3 - 0.6
✅ CARA Decision: RETRAIN_INCREMENTAL
✅ Action: Incremental retraining triggered
```

### What to Show Judges:
- **Drift Detection Tab**: Yellow/Orange status, moderate drift
- **CARA Analysis Tab**: RETRAIN_INCREMENTAL decision
- **Model Retraining Tab**: Shows incremental retrain in progress
- **Drift History Chart**: Second data point shows increase
- **Audit Log**: Shows retraining triggered

---

## 📊 TEST CASE 3: EXTREME DRIFT (Full Retrain)
**Purpose**: Show full retraining for severe drift - **THIS IS THE KEY DEMO!**

### Steps:
1. Go to **"Upload Custom File"** section (bottom of page)
2. Click **"Choose File"** button
3. Navigate to: `extreme_drift/extreme_drift_50K.parquet`
4. Enter Batch ID: `extreme_drift_001`
5. Click **"Upload & Analyze"** button
6. Wait for processing (~8-10 seconds)

### Expected Results:
```
✅ Batch ID: extreme_drift_001
✅ Rows: 50,000
✅ Fraud Rate: 21.14% (+252% vs baseline!)
✅ Mean Amount: $1,854 (+1004% vs baseline!)
✅ International: 35.33% (+607% vs baseline!)
✅ Drift Ratio: 70-90% (EXTREME!)
✅ Severity: SIGNIFICANT
✅ CARA Score: > 0.7
✅ CARA Decision: RETRAIN_FULL ✅
✅ Action: FULL retraining triggered automatically!
```

### What to Show Judges:
- **Drift Detection Tab**: RED status, extreme drift warning
- **CARA Analysis Tab**: RETRAIN_FULL decision with high confidence
- **Model Retraining Tab**: Shows FULL retrain in progress
- **Drift History Chart**: Dramatic spike in drift
- **Audit Log**: Shows full retraining triggered
- **Excel File**: Open `extreme_drift_50K.xlsx` to show data characteristics

---

## 📈 Drift Comparison Table

| Metric | Baseline | Moderate Drift | Extreme Drift | Change (Extreme) |
|--------|----------|----------------|---------------|------------------|
| **Fraud Rate** | 6.04% | 9.11% | 21.14% | **+252%** |
| **Mean Amount** | $168 | ~$250 | $1,854 | **+1004%** |
| **International** | 5% | ~8% | 35.33% | **+607%** |
| **Transaction Count** | 5 | ~7 | 15 | **+200%** |
| **Drift Ratio** | 0-5% | 15-30% | 70-90% | **EXTREME** |
| **CARA Decision** | DEFER | INCREMENTAL | **FULL** | ✅ |

---

## 🎬 Demo Script for Judges

### Introduction (30 seconds)
> "We've built an intelligent ML Auto-Retrain system that monitors data drift and automatically decides when and how to retrain models. Let me show you three scenarios."

### Scenario 1: Clean Data (1 minute)
> "First, let's upload clean baseline data. [Click Upload Original Batch]
> 
> As you can see, the system detects minimal drift (under 5%), and CARA decides to DEFER retraining. The model is still performing well, so no action is needed. This saves computational resources."

### Scenario 2: Moderate Drift (1 minute)
> "Now let's upload data with moderate drift. [Click Upload Drifted Batch]
> 
> Notice the fraud rate increased from 6% to 9% - a 51% increase. The system detects moderate drift (around 20-25%) and CARA recommends INCREMENTAL retraining. This updates the model with new patterns while preserving existing knowledge."

### Scenario 3: Extreme Drift (2 minutes)
> "Finally, let me show you what happens with extreme drift. [Upload extreme_drift_50K.parquet]
> 
> This batch has dramatically different characteristics:
> - Fraud rate jumped to 21% - that's 252% higher!
> - Transaction amounts are 10x higher
> - International transactions increased 6x
> 
> The system detects 70-90% drift ratio and CARA immediately triggers FULL retraining. This completely rebuilds the model because the data distribution has fundamentally changed.
> 
> [Show Excel file] Here's the data I'm showing you - you can see the extreme differences in the 'Drift Comparison' sheet."

### Conclusion (30 seconds)
> "The system automatically handles all three scenarios: defer when stable, incremental updates for moderate changes, and full retraining for major shifts. This ensures models stay accurate without manual intervention."

---

## 🔍 Key Features to Highlight

### 1. **Automated Decision Making**
- CARA algorithm analyzes drift and makes intelligent decisions
- No manual intervention required
- Considers multiple factors: drift ratio, severity, confidence

### 2. **Three-Tier Response**
- **DEFER**: Save resources when model is still good
- **INCREMENTAL**: Quick updates for moderate drift
- **FULL**: Complete rebuild for major changes

### 3. **Real-Time Monitoring**
- Live drift detection on every batch
- Historical tracking with charts
- Audit log for compliance

### 4. **Production Ready**
- Handles large datasets (50K-100K rows)
- Fast processing (8-15 seconds)
- Multiple file formats (Parquet, CSV, Excel)

---

## 📝 Troubleshooting

### If Upload Buttons Don't Work:
1. Check server is running: `http://localhost:8080/health`
2. Check files exist in `data/large_scale/`
3. Check browser console for errors

### If Custom Upload Fails:
1. Verify file path: `extreme_drift/extreme_drift_50K.parquet`
2. Check file size (should be ~2.45 MB)
3. Try with batch ID: `extreme_drift_001`

### If Charts Don't Update:
1. Refresh the page
2. Check browser console for JavaScript errors
3. Verify API responses in Network tab

---

## 📊 Excel Files for Judges

### Custom Test File (10K rows)
**Location**: `custom_uploads/custom_test_10K.xlsx`
**Sheets**:
1. **Data Sample**: 1,000 rows of actual data
2. **Summary Statistics**: Key metrics
3. **Fraud Analysis**: Fraud patterns
4. **Column Descriptions**: Data dictionary

### Extreme Drift File (50K rows)
**Location**: `extreme_drift/extreme_drift_50K.xlsx`
**Sheets**:
1. **Data Sample**: 1,000 rows of extreme drift data
2. **Summary**: Overall statistics
3. **Drift Comparison**: Side-by-side comparison with baseline

---

## ✅ Success Criteria

After completing all three test cases, you should have:

- ✅ 3+ data points in Drift History chart
- ✅ Multiple entries in Audit Log
- ✅ At least one RETRAIN_FULL decision shown
- ✅ Clear visualization of drift progression
- ✅ Demonstrated all three CARA decisions

---

## 🎯 Key Takeaways for Judges

1. **Intelligent Automation**: System makes smart decisions without human intervention
2. **Resource Efficiency**: Only retrains when necessary (DEFER saves compute)
3. **Adaptive Response**: Different strategies for different drift levels
4. **Production Scale**: Handles 50K-100K row batches in seconds
5. **Transparency**: Full audit trail and explainable decisions
6. **Real-World Ready**: Handles extreme scenarios that would break naive systems

---

## 📞 Quick Reference

| Action | Command/URL |
|--------|-------------|
| **Open Dashboard** | `http://localhost:8080` |
| **Check Server** | `http://localhost:8080/health` |
| **Upload Original** | Click "Upload Original Batch" button |
| **Upload Drifted** | Click "Upload Drifted Batch" button |
| **Upload Custom** | Use file picker → `extreme_drift/extreme_drift_50K.parquet` |
| **View Excel** | Open `extreme_drift/extreme_drift_50K.xlsx` |

---

**Last Updated**: April 15, 2026
**Status**: ✅ All test files ready
**Demo Time**: ~5 minutes for all three scenarios
