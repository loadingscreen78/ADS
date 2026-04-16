# 🚀 QUICK DEMO GUIDE - 5 MINUTES

## ✅ SYSTEM STATUS
- **Dashboard:** http://localhost:8080 ✅ RUNNING
- **API Server:** Port 8080 ✅ RUNNING
- **All Tests:** ✅ PASSED

---

## 🎬 DEMO SCRIPT (5 Minutes)

### **1. Introduction (30 seconds)**
**Say:** "We built a research-based ML auto-retrain system implementing three peer-reviewed papers from arXiv."

**Show:** Research papers on screen

---

### **2. Large-Scale Data (1 minute)**
**Say:** "We generated 100,000 row datasets with controlled drift patterns."

**Run:**
```bash
python -c "
import pandas as pd
orig = pd.read_parquet('data/large_scale/original_100K.parquet')
drift = pd.read_parquet('data/large_scale/drifted_100K.parquet')
print(f'Original: {len(orig):,} rows, {orig[\"is_fraud\"].mean():.2%} fraud')
print(f'Drifted: {len(drift):,} rows, {drift[\"is_fraud\"].mean():.2%} fraud')
print(f'Amount drift: +{(drift[\"amount\"].mean() / orig[\"amount\"].mean() - 1) * 100:.1f}%')
"
```

**Expected:**
```
Original: 100,000 rows, 6.04% fraud
Drifted: 100,000 rows, 9.11% fraud
Amount drift: +37.5%
```

---

### **3. File Upload API (1 minute)**
**Say:** "The system accepts batch data uploads via API."

**Run:**
```bash
python test_upload_api.py
```

**Expected:**
```
✅ System status working!
✅ File upload working!
  Rows: 100,000
  Fraud Rate: 6.04%
✅ List batches working!
```

---

### **4. Self-Healing (1.5 minutes)**
**Say:** "When drift is detected, the system automatically diagnoses and fixes issues."

**Run:**
```bash
python demo_research_system.py
```

**Expected:**
```
✅ File upload system working!
✅ Self-healing pipeline working!
  Initial: HEALTHY (95% accuracy)
  After Drift: CRITICAL (88% accuracy)
  Issues: 3 found
  Remediation: 3 actions executed
```

---

### **5. Dashboard (1 minute)**
**Say:** "The dashboard provides real-time monitoring."

**Show:** http://localhost:8080
- Overview tab
- Drift Detection tab
- CARA Scheduler tab
- Fairness tab

---

## 🎯 KEY MESSAGES

1. **Research-Based** ✅
   - 3 peer-reviewed papers from arXiv
   - Self-Healing ML, CARA, Multi-Model

2. **Large-Scale** ✅
   - 100,000 rows
   - Controlled drift (+37.5% amount, +50.5% fraud)

3. **Self-Healing** ✅
   - Automatic diagnosis
   - Automatic remediation
   - 3 issues fixed in demo

4. **File Upload** ✅
   - API endpoint working
   - 100K rows uploaded
   - Metadata extracted

5. **Production-Ready** 85%
   - Dashboard running
   - API working
   - All tests passed

---

## 📊 QUICK STATS

**Datasets:**
- Original: 100K rows, 6.04% fraud
- Drifted: 100K rows, 9.11% fraud (+50.5%)

**Performance:**
- File upload: ~1 second
- Drift detection: 0.23 seconds
- Self-healing: <1 second

**Components:**
- ✅ File Upload
- ✅ Self-Healing
- ✅ Drift Detection
- ✅ CARA Scheduler
- ✅ Fairness Monitoring

---

## 🔧 QUICK COMMANDS

**Test Everything:**
```bash
python test_upload_api.py
```

**Run Demo:**
```bash
python demo_research_system.py
```

**Open Dashboard:**
```
http://localhost:8080
```

**Check Status:**
```bash
curl http://localhost:8080/api/status
```

---

## 🏆 FINAL CHECKLIST

- [x] Server running
- [x] Datasets generated
- [x] API tested
- [x] Self-healing tested
- [x] File upload tested
- [x] Dashboard accessible

**STATUS:** 🚀 READY TO DEMO!

---

**GO SHOW THE JUDGES! 🎉**

