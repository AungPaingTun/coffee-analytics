"""
Coffee Analytics Platform - Main Entry Point
Starts the FastAPI server. Railway calls: uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import init_db

# Initialize database on import
init_db()

# Import the FastAPI app
from api.app import app
