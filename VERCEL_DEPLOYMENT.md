# 🚀 Vercel Deployment Guide

## ✅ Vercel-Ready Files Created

### 1. `api/app.py` - Simplified FastAPI App
- **Purpose**: Serverless-compatible version for Vercel
- **Features**: Demo mode with simulated drift detection
- **Size**: Lightweight, no large data files required

### 2. `api/index.py` - Alternative Entry Point
- **Purpose**: Full-featured app (requires data files)
- **Note**: May exceed Vercel limits

### 3. `vercel.json` - Deployment Configuration
- **Routes**: API and dashboard routing
- **Memory**: 1024 MB
- **Timeout**: 30 seconds

### 4. `requirements.txt` - Python Dependencies
- **Core**: FastAPI, Uvicorn, Pandas
- **ML**: scikit-learn, TensorFlow
- **Total**: ~20 packages

---

## 🎯 Deployment Options

### Option 1: Demo Mode (Recommended for Vercel)
Uses `api/app.py` - simplified version without data files

**Pros**:
- ✅ Fast deployment
- ✅ No large files
- ✅ Works within Vercel limits
- ✅ Demo functionality

**Cons**:
- ⚠️ Simulated drift detection
- ⚠️ No real model training

### Option 2: Full Mode
Uses `api/index.py` - full system with data files

**Pros**:
- ✅ Real drift detection
- ✅ Actual model training
- ✅ Complete features

**Cons**:
- ⚠️ Large deployment size
- ⚠️ May exceed Vercel limits
- ⚠️ Slower cold starts

---

## 📦 What's Deployed

### API Endpoints (Demo Mode)
```
GET  /                    - Dashboard HTML
GET  /health              - Health check
GET  /api/metrics         - Current metrics
GET  /api/drift/history   - Drift history
GET  /api/cara/decision   - CARA decision
GET  /api/alerts          - System alerts
POST /api/upload/batch    - Upload batch (demo)
POST /api/upload/process/{id} - Process batch (demo)
POST /api/upload/quick/{type}  - Quick upload (demo)
GET  /api/info            - System information
```

### Dashboard
- Real-time monitoring interface
- Interactive charts
- Upload functionality
- Drift history visualization

---

## 🚀 Deploy to Vercel

### Method 1: Vercel Dashboard (Easiest)

1. **Go to Vercel**: https://vercel.com
2. **Import Project**: Click "Add New" → "Project"
3. **Connect GitHub**: Select `loadingscreen78/ADS`
4. **Configure**:
   - Framework Preset: Other
   - Build Command: (leave empty)
   - Output Directory: (leave empty)
5. **Deploy**: Click "Deploy"

### Method 2: Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
vercel

# Production deployment
vercel --prod
```

### Method 3: GitHub Integration (Automatic)

1. Connect Vercel to your GitHub repository
2. Every push to `main` branch auto-deploys
3. Pull requests get preview deployments

---

## ⚙️ Configuration

### Environment Variables (Optional)

In Vercel Dashboard → Settings → Environment Variables:

```
CARA_FULL_RETRAIN_THRESHOLD=0.7
CARA_INCREMENTAL_THRESHOLD=0.4
PSI_THRESHOLD=0.1
```

### Custom Domain (Optional)

1. Go to Vercel Dashboard → Settings → Domains
2. Add your custom domain
3. Configure DNS records

---

## 🔍 Troubleshooting

### Build Fails: "No fastapi entrypoint found"
**Solution**: Ensure `api/app.py` exists and exports `app`

### Build Fails: "Module not found"
**Solution**: Check `requirements.txt` has all dependencies

### Deployment Too Large
**Solution**: Use demo mode (`api/app.py`) instead of full mode

### Cold Start Timeout
**Solution**: Reduce memory or increase timeout in `vercel.json`

### API Not Working
**Solution**: Check routes in `vercel.json` match your endpoints

---

## 📊 Vercel Limits

### Free Tier:
- **Bandwidth**: 100 GB/month
- **Invocations**: 100 GB-hours
- **Execution Time**: 10 seconds max
- **Deployment Size**: 100 MB

### Pro Tier:
- **Bandwidth**: 1 TB/month
- **Invocations**: 1000 GB-hours
- **Execution Time**: 60 seconds max
- **Deployment Size**: 250 MB

**Our App (Demo Mode)**:
- Size: ~50 MB
- Execution: <5 seconds
- ✅ Fits in Free Tier

---

## 🎯 Demo Mode Features

### What Works:
- ✅ Dashboard interface
- ✅ Upload simulation
- ✅ Drift detection (simulated)
- ✅ CARA decisions (simulated)
- ✅ Real-time charts
- ✅ Audit logging
- ✅ All API endpoints

### What's Simulated:
- ⚠️ Drift detection (returns preset values)
- ⚠️ Model training (not executed)
- ⚠️ File processing (metadata only)

### Perfect For:
- 🎓 Demonstrations
- 📊 Presentations
- 🎮 Interactive demos
- 📱 Portfolio showcase

---

## 🔗 After Deployment

### Your URLs:
```
Production: https://your-project.vercel.app
Dashboard:  https://your-project.vercel.app/
API Docs:   https://your-project.vercel.app/docs
Health:     https://your-project.vercel.app/health
```

### Test Deployment:
```bash
# Health check
curl https://your-project.vercel.app/health

# Get metrics
curl https://your-project.vercel.app/api/metrics

# System info
curl https://your-project.vercel.app/api/info
```

---

## 📱 Share Your Deployment

### For Poster:
Generate QR code for: `https://your-project.vercel.app`

### For Resume:
```
Live Demo: https://your-project.vercel.app
GitHub: https://github.com/loadingscreen78/ADS
```

### For Presentation:
```
🚀 Live Demo Available!
Scan QR code or visit:
https://your-project.vercel.app
```

---

## 🔄 Update Deployment

### Automatic (Recommended):
1. Push changes to GitHub
2. Vercel auto-deploys
3. Check deployment status in Vercel Dashboard

### Manual:
```bash
vercel --prod
```

---

## 📊 Monitoring

### Vercel Dashboard:
- **Analytics**: View traffic and performance
- **Logs**: Real-time function logs
- **Deployments**: History of all deployments
- **Domains**: Manage custom domains

### Check Status:
```bash
vercel ls
vercel inspect <deployment-url>
```

---

## 🎓 Best Practices

1. **Use Demo Mode** for Vercel (lightweight)
2. **Enable Analytics** in Vercel Dashboard
3. **Set up Custom Domain** for professional look
4. **Monitor Logs** for errors
5. **Test Before Production** using preview deployments
6. **Keep Dependencies Minimal** to reduce size
7. **Use Environment Variables** for configuration

---

## 🆘 Support

### Vercel Documentation:
- https://vercel.com/docs
- https://vercel.com/docs/frameworks/backend/fastapi

### Common Issues:
- Build errors: Check `requirements.txt`
- Runtime errors: Check function logs
- Timeout errors: Reduce processing time
- Size errors: Remove large files

---

## ✅ Deployment Checklist

- [x] `api/app.py` created (simplified version)
- [x] `api/index.py` created (full version)
- [x] `vercel.json` configured
- [x] `requirements.txt` updated
- [x] `.gitignore` excludes large files
- [ ] Push to GitHub
- [ ] Connect Vercel to GitHub
- [ ] Deploy to Vercel
- [ ] Test deployment
- [ ] Add custom domain (optional)
- [ ] Update poster with live URL

---

## 🎉 Ready to Deploy!

Your project is now Vercel-ready!

**Next Steps**:
1. Push changes to GitHub
2. Connect Vercel to your repository
3. Deploy and get your live URL
4. Share with judges and on your poster!

---

**Files Created**:
- ✅ `api/app.py` - Serverless FastAPI app
- ✅ `api/index.py` - Full app entry point
- ✅ `vercel.json` - Deployment config
- ✅ `requirements.txt` - Dependencies
- ✅ `VERCEL_DEPLOYMENT.md` - This guide

**Status**: ✅ Ready for Vercel Deployment

**Authors**: Jagannath Mishra (RA101), Suhil R (RA093)
