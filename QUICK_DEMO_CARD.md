# 🎯 QUICK DEMO CARD - Keep This Open During Demo!

---

## 🚀 DEMO FLOW (5 Minutes)

### 1️⃣ BASELINE - DEFER (1 min)
```
Action: Click "Upload Original Batch"
Result: DEFER ✅
Message: "Model is stable, no retraining needed"
```

### 2️⃣ MODERATE - INCREMENTAL (1 min)
```
Action: Click "Upload Drifted Batch"
Result: RETRAIN_INCREMENTAL ✅
Message: "Moderate drift detected, incremental update triggered"
```

### 3️⃣ EXTREME - FULL RETRAIN (2 min) ⭐
```
Action: Upload Custom File
File: extreme_drift/extreme_drift_50K.parquet
Batch ID: extreme_drift_001
Result: RETRAIN_FULL ✅
Message: "EXTREME drift detected, full retraining triggered!"
```

---

## 📊 KEY NUMBERS TO MENTION

| Metric | Baseline | Extreme | Change |
|--------|----------|---------|--------|
| **Fraud Rate** | 6% | 21% | **+252%** |
| **Amount** | $168 | $1,854 | **+1004%** |
| **International** | 5% | 35% | **+607%** |

---

## 🎤 TALKING POINTS

### Opening
> "We built an intelligent system that automatically detects data drift and decides when to retrain ML models. Let me show you three scenarios."

### Test 1 (DEFER)
> "Clean data, minimal drift. System says: don't waste resources, model is still good."

### Test 2 (INCREMENTAL)
> "Moderate drift, fraud increased 51%. System says: update the model incrementally."

### Test 3 (FULL) ⭐
> "Extreme drift - fraud tripled, amounts 10x higher. System says: complete rebuild needed. This simulates a real crisis like a pandemic or new fraud ring."

### Closing
> "Three intelligent decisions, fully automated, no manual intervention. The system handles everything from stable conditions to crisis scenarios."

---

## 📁 FILE PATHS (Copy-Paste Ready)

```
Dashboard: http://localhost:8080
Extreme Batch: extreme_drift/extreme_drift_50K.parquet
Excel File: extreme_drift/extreme_drift_50K.xlsx
Batch ID: extreme_drift_001
```

---

## ✅ EXPECTED RESULTS

### Test 1: Original Batch
- Drift: 0-5%
- Decision: **DEFER**
- Time: ~10 seconds

### Test 2: Drifted Batch
- Drift: 15-30%
- Decision: **RETRAIN_INCREMENTAL**
- Time: ~10 seconds

### Test 3: Extreme Batch ⭐
- Drift: 70-90%
- Decision: **RETRAIN_FULL**
- Time: ~8 seconds

---

## 🔥 IF SOMETHING GOES WRONG

### Upload Fails?
- Refresh page (F5)
- Check server: http://localhost:8080/health
- Try again

### Chart Not Updating?
- Refresh page (F5)
- Check browser console (F12)

### Need to Restart?
- Close browser
- Restart server
- Open dashboard again

---

## 🎯 SUCCESS CRITERIA

- ✅ All 3 uploads complete
- ✅ All 3 decisions shown (DEFER, INCREMENTAL, FULL)
- ✅ Drift chart shows progression
- ✅ Judges see RETRAIN_FULL triggered

---

**YOU GOT THIS! 🚀**

Dashboard: http://localhost:8080
