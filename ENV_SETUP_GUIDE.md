# 🔧 Environment Configuration Guide

## About .env69

The `.env69` file contains all configuration settings for the ML Auto-Retrain System. It's named `.env69` to avoid conflicts with actual `.env` files and to serve as a template.

---

## 🚀 Quick Setup

### Option 1: Use Default Settings (Recommended)
The system works out-of-the-box without any .env file. All settings have sensible defaults.

### Option 2: Customize Settings
If you want to customize settings:

1. **Copy the template**:
   ```bash
   cp .env69 .env
   ```

2. **Edit .env** with your preferred settings

3. **Restart the server** to apply changes

---

## 📋 Key Configuration Sections

### 1. Server Configuration
```env
API_HOST=0.0.0.0        # Listen on all interfaces
API_PORT=8080           # Dashboard port
DEBUG=False             # Enable debug mode
```

### 2. CARA Algorithm Thresholds
```env
CARA_FULL_RETRAIN_THRESHOLD=0.7    # Score >= 0.7 → FULL_RETRAIN
CARA_INCREMENTAL_THRESHOLD=0.4     # Score >= 0.4 → INCREMENTAL
CARA_DEFER_THRESHOLD=0.2           # Score >= 0.2 → DEFER
```

**Adjust these to make CARA more/less aggressive**:
- **More aggressive**: Lower thresholds (e.g., 0.6, 0.3, 0.1)
- **Less aggressive**: Higher thresholds (e.g., 0.8, 0.5, 0.3)

### 3. Drift Detection Parameters
```env
KS_SIGNIFICANCE_LEVEL=0.05    # p-value threshold for KS test
PSI_THRESHOLD=0.1             # PSI threshold for drift
MIN_SAMPLES=1000              # Minimum samples required
```

### 4. File Upload Limits
```env
MAX_UPLOAD_SIZE_MB=100              # Maximum file size
SUPPORTED_FORMATS=.parquet,.csv     # Allowed formats
```

### 5. Performance Settings
```env
USE_GPU=False          # Enable GPU acceleration
N_WORKERS=4            # Parallel workers
BATCH_SIZE=10000       # Processing batch size
```

---

## 🎯 Common Customizations

### Make CARA More Sensitive to Drift
```env
CARA_FULL_RETRAIN_THRESHOLD=0.6
CARA_INCREMENTAL_THRESHOLD=0.3
CARA_DEFER_THRESHOLD=0.1
PSI_THRESHOLD=0.08
```

### Make CARA Less Sensitive (More Conservative)
```env
CARA_FULL_RETRAIN_THRESHOLD=0.8
CARA_INCREMENTAL_THRESHOLD=0.5
CARA_DEFER_THRESHOLD=0.3
PSI_THRESHOLD=0.15
```

### Enable GPU Acceleration
```env
USE_GPU=True
```
*Requires CUDA-compatible GPU and drivers*

### Increase Upload Limit
```env
MAX_UPLOAD_SIZE_MB=500
```

### Enable Production Mode
```env
PRODUCTION=True
DEBUG=False
WORKERS=8
WORKER_TIMEOUT=600
```

---

## 🔐 Security Settings

### Enable API Authentication
```env
API_KEY=your-secret-key-here
```

Then include in API requests:
```bash
curl -H "X-API-Key: your-secret-key-here" http://localhost:8080/api/...
```

### Restrict CORS Origins
```env
ENABLE_CORS=True
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

---

## 📧 Notifications (Optional)

### Email Alerts
```env
ENABLE_EMAIL_NOTIFICATIONS=True
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
NOTIFICATION_EMAIL=alerts@yourdomain.com
```

### Slack Alerts
```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

---

## 🗄️ Database Configuration (Production)

### PostgreSQL
```env
DATABASE_URL=postgresql://user:password@localhost:5432/ml_retrain
```

### Redis Cache
```env
REDIS_URL=redis://localhost:6379/0
```

---

## 🐳 Docker Configuration

### Custom Network
```env
DOCKER_NETWORK=my-ml-network
DRIFT_MONITOR_CONTAINER=my-drift-monitor
RETRAIN_ENGINE_CONTAINER=my-retrain-engine
```

---

## 📊 Monitoring Settings

### Retention Periods
```env
DRIFT_HISTORY_DAYS=180      # Keep 6 months of drift history
AUDIT_LOG_DAYS=730          # Keep 2 years of audit logs
```

### Logging
```env
LOG_LEVEL=DEBUG             # More verbose logging
LOG_FILE=logs/debug.log
LOG_TO_CONSOLE=True
```

---

## 🧪 Development Settings

### Enable Hot Reload
```env
HOT_RELOAD=True
DEBUG_MODE=True
ENABLE_PROFILING=True
```

---

## ⚙️ Advanced Features

### Enable All Features
```env
ENABLE_LSTM_PREDICTION=True      # Predictive drift forecasting
ENABLE_ENSEMBLE=True             # Multi-model ensemble
ENABLE_SELF_HEALING=True         # Auto-remediation
ENABLE_FAIRNESS_MONITORING=True  # Bias detection
```

---

## 🔍 Troubleshooting

### Server Won't Start
Check:
- Port 8080 is not in use: `netstat -ano | findstr :8080`
- Paths exist: `data/`, `data/models/`, `data/uploads/`
- Permissions are correct

### Configuration Not Applied
1. Ensure file is named `.env` (not `.env69`)
2. Restart the server
3. Check for syntax errors in .env file
4. Verify environment variables are loaded:
   ```python
   import os
   print(os.getenv('API_PORT'))
   ```

### GPU Not Working
1. Check CUDA installation: `nvidia-smi`
2. Install GPU-enabled packages:
   ```bash
   pip install tensorflow-gpu
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

---

## 📝 Environment Variable Priority

Settings are loaded in this order (later overrides earlier):

1. **Default values** (in code)
2. **.env file** (if exists)
3. **System environment variables**
4. **Command-line arguments**

Example:
```bash
# Override port via environment variable
API_PORT=9000 python src/services/api_server.py

# Override via command line
python src/services/api_server.py --port 9000
```

---

## 🎯 Recommended Settings by Use Case

### Development
```env
DEBUG=True
HOT_RELOAD=True
LOG_LEVEL=DEBUG
ENABLE_CORS=True
```

### Testing
```env
DEBUG=False
LOG_LEVEL=INFO
MIN_SAMPLES=100
BATCH_SIZE=1000
```

### Production
```env
PRODUCTION=True
DEBUG=False
LOG_LEVEL=WARNING
WORKERS=8
USE_GPU=True
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
ENABLE_EMAIL_NOTIFICATIONS=True
API_KEY=your-secret-key
```

### Demo/Presentation
```env
DEBUG=False
LOG_LEVEL=INFO
ENABLE_MONITORING=True
HOT_RELOAD=False
```

---

## 🔄 Applying Changes

### Method 1: Restart Server
```bash
# Stop server (Ctrl+C)
# Start again
python src/services/api_server.py
```

### Method 2: Reload Configuration (if supported)
```bash
curl -X POST http://localhost:8080/api/admin/reload-config
```

### Method 3: Docker Restart
```bash
docker-compose restart
```

---

## ✅ Validation

### Check Current Configuration
```bash
curl http://localhost:8080/api/config
```

### Test Configuration
```python
from dotenv import load_dotenv
import os

load_dotenv('.env')

print(f"API Port: {os.getenv('API_PORT')}")
print(f"CARA Threshold: {os.getenv('CARA_FULL_RETRAIN_THRESHOLD')}")
print(f"Use GPU: {os.getenv('USE_GPU')}")
```

---

## 📚 Additional Resources

- **Python-dotenv**: https://pypi.org/project/python-dotenv/
- **Environment Variables Best Practices**: https://12factor.net/config
- **FastAPI Configuration**: https://fastapi.tiangolo.com/advanced/settings/

---

## 🆘 Support

If you need help with configuration:

1. Check the logs: `logs/app.log`
2. Verify .env syntax (no spaces around `=`)
3. Ensure values are properly quoted if they contain spaces
4. Check for typos in variable names

---

**File**: `.env69` (template)  
**Usage**: Copy to `.env` and customize  
**Status**: ✅ Template ready  
**Default**: System works without .env file
