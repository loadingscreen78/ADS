"""
Simplified FastAPI App for Vercel Deployment
This version works without large data files
"""

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import json
from datetime import datetime
from pathlib import Path

# Create FastAPI app
app = FastAPI(
    title="ML Auto-Retrain Dashboard API",
    version="1.0.0",
    description="Context-Aware Retraining Algorithm (CARA) System"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple state management
class SystemState:
    def __init__(self):
        self.current_metrics = {
            "accuracy": 0.951,
            "auc": 0.906,
            "drift_ratio": 0.0,
            "model_version": "v8",
            "processed_batches": 0,
            "severity": "NONE",
            "current_drift": "0.0%",
            "cara_decision": "NO_ACTION",
            "cara_score": 0.0,
            "training_time": "1.23s"
        }
        self.drift_history = []
        self.alerts = []

state = SystemState()

# Root endpoint - serve dashboard
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the dashboard HTML"""
    try:
        dashboard_path = Path(__file__).parent.parent / "dashboard.html"
        if dashboard_path.exists():
            return dashboard_path.read_text()
        return """
        <html>
            <head><title>ML Auto-Retrain System</title></head>
            <body>
                <h1>ML Auto-Retrain System with CARA</h1>
                <p>Dashboard loading...</p>
                <p>API is running at <a href="/docs">/docs</a></p>
            </body>
        </html>
        """
    except Exception as e:
        return f"<html><body><h1>Error loading dashboard</h1><p>{str(e)}</p></body></html>"

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "service": "ML Auto-Retrain CARA System"
    }

# Get current metrics
@app.get("/api/metrics")
async def get_metrics():
    """Get current system metrics"""
    return {
        "success": True,
        "metrics": state.current_metrics,
        "timestamp": datetime.now().isoformat()
    }

# Get drift history
@app.get("/api/drift/history")
async def get_drift_history():
    """Get drift detection history"""
    return {
        "success": True,
        "history": state.drift_history,
        "total": len(state.drift_history)
    }

# Get CARA decision
@app.get("/api/cara/decision")
async def get_cara_decision():
    """Get current CARA decision"""
    return {
        "success": True,
        "decision": state.current_metrics["cara_decision"],
        "score": state.current_metrics["cara_score"],
        "drift_ratio": state.current_metrics["drift_ratio"],
        "severity": state.current_metrics["severity"]
    }

# Get alerts
@app.get("/api/alerts")
async def get_alerts():
    """Get system alerts"""
    return {
        "success": True,
        "alerts": state.alerts[-10:],  # Last 10 alerts
        "total": len(state.alerts)
    }

# Upload batch (simplified for demo)
@app.post("/api/upload/batch")
async def upload_batch(
    file: UploadFile = File(...),
    batch_id: Optional[str] = Form(None)
):
    """Upload a batch file (demo mode)"""
    try:
        # Generate batch ID if not provided
        if not batch_id:
            batch_id = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Simulate processing
        metadata = {
            "n_rows": 50000,
            "n_columns": 14,
            "fraud_rate": 0.21,
            "file_size": file_size,
            "filename": file.filename
        }
        
        # Add alert
        state.alerts.append({
            "timestamp": datetime.now().isoformat(),
            "type": "batch_uploaded",
            "severity": "INFO",
            "message": f"Batch {batch_id} uploaded: {metadata['n_rows']:,} rows"
        })
        
        return {
            "success": True,
            "batch_id": batch_id,
            "metadata": metadata,
            "message": f"Successfully uploaded {metadata['n_rows']:,} rows"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Process batch (simplified for demo)
@app.post("/api/upload/process/{batch_id}")
async def process_batch(batch_id: str):
    """Process uploaded batch (demo mode)"""
    try:
        # Simulate drift detection
        drift_ratio = 0.857  # 85.7% drift
        severity = "CRITICAL"
        cara_score = 0.729
        cara_decision = "FULL_RETRAIN"
        
        # Update state
        state.current_metrics.update({
            "drift_ratio": drift_ratio,
            "severity": severity,
            "cara_score": cara_score,
            "cara_decision": cara_decision,
            "processed_batches": state.current_metrics["processed_batches"] + 1
        })
        
        # Add to history
        state.drift_history.append({
            "timestamp": datetime.now().isoformat(),
            "batch_id": batch_id,
            "drift_ratio": drift_ratio,
            "severity": severity,
            "cara_score": cara_score,
            "decision": cara_decision
        })
        
        # Add alert
        state.alerts.append({
            "timestamp": datetime.now().isoformat(),
            "type": "drift_detected",
            "severity": severity,
            "message": f"Batch {batch_id}: {severity} drift ({drift_ratio:.1%})"
        })
        
        return {
            "success": True,
            "batch_id": batch_id,
            "drift_ratio": drift_ratio,
            "severity": severity,
            "cara_decision": cara_decision,
            "cara_score": cara_score,
            "message": "Analysis complete"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Quick upload endpoints
@app.post("/api/upload/quick/{batch_type}")
async def quick_upload(batch_type: str):
    """Quick upload pre-configured batches (demo mode)"""
    try:
        if batch_type == "original":
            drift_ratio = 0.023
            severity = "LOW"
            cara_score = 0.234
            cara_decision = "DEFER"
            fraud_rate = 0.0604
        elif batch_type == "drifted":
            drift_ratio = 0.247
            severity = "MODERATE"
            cara_score = 0.487
            cara_decision = "INCREMENTAL"
            fraud_rate = 0.0911
        else:
            return {"success": False, "error": "Invalid batch type"}
        
        batch_id = f"{batch_type}_batch"
        
        # Update state
        state.current_metrics.update({
            "drift_ratio": drift_ratio,
            "severity": severity,
            "cara_score": cara_score,
            "cara_decision": cara_decision,
            "processed_batches": state.current_metrics["processed_batches"] + 1
        })
        
        # Add to history
        state.drift_history.append({
            "timestamp": datetime.now().isoformat(),
            "batch_id": batch_id,
            "drift_ratio": drift_ratio,
            "severity": severity,
            "cara_score": cara_score,
            "decision": cara_decision
        })
        
        return {
            "success": True,
            "batch_id": batch_id,
            "metadata": {
                "n_rows": 100000,
                "fraud_rate": fraud_rate
            },
            "drift_score": {
                "drift_ratio": drift_ratio,
                "overall_severity": severity
            },
            "cara_decision": {
                "decision": cara_decision,
                "score": cara_score,
                "expected_gain": 0.043,
                "justification": f"CARA score {cara_score:.3f}. Drift severity: {severity}."
            },
            "metrics": state.current_metrics
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# System info
@app.get("/api/info")
async def system_info():
    """Get system information"""
    return {
        "name": "ML Auto-Retrain System with CARA",
        "version": "1.0.0",
        "authors": ["Jagannath Mishra (RA101)", "Suhil R (RA093)"],
        "description": "Context-Aware Retraining Algorithm for automated drift detection and model retraining",
        "features": [
            "Dual drift detection (KS + PSI)",
            "CARA algorithm with multi-factor scoring",
            "Three-tier adaptive retraining",
            "Real-time monitoring dashboard",
            "REST API with FastAPI"
        ],
        "github": "https://github.com/loadingscreen78/ADS",
        "deployment": "Vercel Serverless",
        "status": "running"
    }

# Export app for Vercel
__all__ = ['app']
