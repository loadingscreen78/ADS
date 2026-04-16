"""
Vercel Serverless Function Entry Point
This file exports the FastAPI app for Vercel deployment
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the FastAPI app
from src.services.api_server import app

# Export for Vercel
# Vercel looks for 'app' variable in this file
__all__ = ['app']
