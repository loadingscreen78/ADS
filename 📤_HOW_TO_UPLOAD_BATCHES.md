# 📤 HOW TO UPLOAD DATA BATCHES

## 📁 DATA BATCH FILES LOCATION

The 2 data batch files are located at:

```
data/large_scale/
├── original_100K.parquet  (5.12 MB, 100K rows, 6.04% fraud)
└── drifted_100K.parquet   (5.12 MB, 100K rows, 9.11% fraud)
```

---

## 🚀 METHOD 1: AUTOMATIC UPLOAD (EASIEST) ✅

**Already Done!** Both batches are uploaded and ready to use.

**Verify:**
```bash
curl http://localhost:8080/api/upload/batches
```

**Expected Output:**
```json
{
  "batches": [
    {
      "batch_id": "original_batch",
      "n_rows": 100000,
      "fraud_rate": 0.0604
    },
    {
      "batch_id": "drifted_batch",
      "n_rows": 100000,
      "fraud_rate": 0.0911
    }
  ],
  "total": 2
}
```

---

## 🎯 METHOD 2: PYTHON SCRIPT (RECOMMENDED)

**Run the upload script:**
```bash
python upload_batches.py
```

**What it does:**
- ✅ Checks server status
- ✅ Uploads original_100K.parquet as "original_batch"
- ✅ Uploads drifted_100K.parquet as "drifted_batch"
- ✅ Shows statistics for each batch

**Output:**
```
✅ Upload Successful!

📊 Batch Statistics:
   Rows: 100,000
   Columns: 15
   Fraud Rate: 6.04%
   Has Target: True
```

---

## 🌐 METHOD 3: WEB INTERFACE

**Open the upload interface:**
```
file:///C:/Users/ASUS/Downloads/project/upload_interface.html
```

Or open `upload_interface.html` in your browser.

**Features:**
- 📤 Drag & drop file upload
- 🆔 Custom batch ID
- ⚡ Quick upload buttons
- 📊 Real-time statistics

---

## 💻 METHOD 4: CURL COMMAND

**Upload original batch:**
```bash
curl -X POST http://localhost:8080/api/upload/batch \
  -F "file=@data/large_scale/original_100K.parquet" \
  -F "batch_id=original_batch"
```

**Upload drifted batch:**
```bash
curl -X POST http://localhost:8080/api/upload/batch \
  -F "file=@data/large_scale/drifted_100K.parquet" \
  -F "batch_id=drifted_batch"
```

---

## 🔍 METHOD 5: PYTHON REQUESTS

**Upload using Python:**
```python
import requests

# Upload file
with open('data/large_scale/original_100K.parquet', 'rb') as f:
    files = {'file': f}
    data = {'batch_id': 'original_batch'}
    response = requests.post(
        'http://localhost:8080/api/upload/batch',
        files=files,
        data=data
    )
    print(response.json())
```

---

## 📊 AFTER UPLOADING - PROCESS THE BATCH

### **Step 1: List Uploaded Batches**
```bash
curl http://localhost:8080/api/upload/batches
```

### **Step 2: Process a Batch for Drift Detection**
```bash
curl -X POST http://localhost:8080/api/upload/process/original_batch
```

**Or:**
```bash
curl -X POST http://localhost:8080/api/upload/process/drifted_batch
```

### **Step 3: View Results**
```bash
# Check drift history
curl http://localhost:8080/api/drift/history

# Check CARA decision
curl http://localhost:8080/api/cara/decision

# Check system status
curl http://localhost:8080/api/status
```

---

## 🎬 COMPLETE DEMO WORKFLOW

### **1. Upload Both Batches**
```bash
python upload_batches.py
```

### **2. Process Original Batch (Baseline)**
```bash
curl -X POST http://localhost:8080/api/upload/process/original_batch
```

**Expected:** Low drift (baseline)

### **3. Process Drifted Batch (With Drift)**
```bash
curl -X POST http://localhost:8080/api/upload/process/drifted_batch
```

**Expected:** High drift detected, auto-retrain triggered

### **4. View Results in Dashboard**
```
http://localhost:8080
```

**What to see:**
- 📊 Drift graphs showing increase
- 🎯 CARA decision (RETRAIN_FULL)
- 🔮 LSTM predictions
- ⚖️ Fairness metrics

---

## 📈 WHAT HAPPENS WHEN YOU UPLOAD?

### **Upload Process:**
1. ✅ File validation (size, format)
2. ✅ Metadata extraction
3. ✅ Fraud rate detection
4. ✅ Statistics calculation
5. ✅ Save to `data/uploads/`
6. ✅ Store metadata in JSON

### **Processing Process:**
1. ✅ Load batch data
2. ✅ Run drift detection (KS Test + PSI)
3. ✅ Calculate drift ratio
4. ✅ Get CARA decision
5. ✅ Auto-retrain if needed
6. ✅ Update dashboard

---

## 🎯 BATCH COMPARISON

### **Original Batch:**
```
File: original_100K.parquet
Rows: 100,000
Fraud Rate: 6.04%
Mean Amount: $168.04
International: 4.99%
```

### **Drifted Batch:**
```
File: drifted_100K.parquet
Rows: 100,000
Fraud Rate: 9.11% (+50.5%)
Mean Amount: $231.03 (+37.5%)
International: 9.85% (+97.4%)
```

### **Drift Characteristics:**
- ✅ **Covariate Drift:** +37.5% in transaction amounts
- ✅ **Concept Drift:** +50.5% in fraud rate
- ✅ **Prior Drift:** +97.4% in international transactions

---

## 🔧 TROUBLESHOOTING

### **Problem: Server not running**
```bash
# Start server
python src/services/api_server.py

# Or check if running
curl http://localhost:8080/api/status
```

### **Problem: File not found**
```bash
# Generate datasets
python generate_datasets_quick.py

# Check files exist
ls data/large_scale/
```

### **Problem: Upload fails**
```bash
# Check file size (should be ~5MB)
ls -lh data/large_scale/

# Check server logs
# Look at terminal where server is running
```

### **Problem: Cannot connect**
```bash
# Check port 8080 is not blocked
netstat -an | findstr 8080

# Try different port (edit api_server.py)
```

---

## 📊 API ENDPOINTS SUMMARY

### **Upload Endpoints:**
- `POST /api/upload/batch` - Upload a batch file
- `GET /api/upload/batches` - List uploaded batches
- `POST /api/upload/process/{batch_id}` - Process uploaded batch

### **Monitoring Endpoints:**
- `GET /api/status` - System status
- `GET /api/drift/history` - Drift history
- `GET /api/cara/decision` - CARA decision
- `GET /api/fairness/metrics` - Fairness metrics

---

## 🎉 QUICK START

**Just run this:**
```bash
# 1. Upload batches
python upload_batches.py

# 2. Process drifted batch
curl -X POST http://localhost:8080/api/upload/process/drifted_batch

# 3. Open dashboard
start http://localhost:8080
```

**That's it!** You'll see:
- ✅ Drift detected
- ✅ CARA decision
- ✅ Auto-retrain triggered
- ✅ Metrics updated

---

## 📁 FILES SUMMARY

**Data Batches:**
- `data/large_scale/original_100K.parquet` - Baseline data
- `data/large_scale/drifted_100K.parquet` - Drifted data

**Upload Tools:**
- `upload_batches.py` - Automatic upload script
- `upload_interface.html` - Web upload interface
- `test_upload_api.py` - API testing script

**Documentation:**
- `📤_HOW_TO_UPLOAD_BATCHES.md` - This file
- `🏆_FINAL_DEMO_READY.md` - Complete demo guide
- `QUICK_DEMO_GUIDE.md` - 5-minute demo script

---

## 🏆 STATUS

**Batches:** ✅ UPLOADED  
**Server:** ✅ RUNNING  
**API:** ✅ WORKING  
**Dashboard:** ✅ ACCESSIBLE  

**You can now:**
- ✅ Upload batches via API
- ✅ Process batches for drift detection
- ✅ View results in dashboard
- ✅ Show judges the complete workflow

---

**Ready to demonstrate! 🚀**

