"""
Simple Dashboard Launcher
Starts the API server and provides instructions
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

print("=" * 80)
print(" " * 20 + "ML AUTO-RETRAIN DASHBOARD")
print(" " * 25 + "Starting System...")
print("=" * 80)
print()

# Check if required packages are installed
try:
    import fastapi
    import uvicorn
    print("[✓] FastAPI installed")
except ImportError:
    print("[!] Installing FastAPI...")
    subprocess.run([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn", "websockets", "-q"])
    print("[✓] FastAPI installed")

print()
print("Starting API server on http://localhost:8080")
print()
print("=" * 80)
print("DASHBOARD INSTRUCTIONS")
print("=" * 80)
print()
print("1. The API server is starting...")
print("2. Open your browser to: http://localhost:8080")
print("3. Or open the dashboard.html file directly")
print()
print("Features:")
print("  • Real-time monitoring via WebSocket")
print("  • Interactive charts and metrics")
print("  • Process batches with one click")
print("  • Train models and LSTM predictor")
print("  • View drift detection results")
print()
print("Press Ctrl+C to stop the server")
print("=" * 80)
print()

# Open browser after a delay
def open_browser():
    time.sleep(2)
    webbrowser.open('http://localhost:8080')

import threading
threading.Thread(target=open_browser, daemon=True).start()

# Start server
import uvicorn
from src.services.api_server import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")