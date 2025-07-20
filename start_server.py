#!/usr/bin/env python3
"""
Startup script for the PricingEngine API server.
This script sets up the Python path and starts the FastAPI server.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now import and run the API
if __name__ == "__main__":
    from api.main import app
    import uvicorn
    
    print("🚀 Starting PricingEngine API server...")
    print(f"📁 Project root: {project_root}")
    print("📊 Features: Traditional Pricing + RAROC Risk-Based Pricing")
    print("🔗 API Documentation: http://localhost:8000/docs")
    print("💡 Health Check: http://localhost:8000/health")
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
