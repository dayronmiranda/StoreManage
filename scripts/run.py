#!/usr/bin/env python3
"""
Startup script for the Store Management API
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    import uvicorn
    
    # Run the FastAPI application
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )