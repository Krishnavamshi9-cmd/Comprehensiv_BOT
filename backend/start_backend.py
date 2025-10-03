#!/usr/bin/env python3
"""
Backend server startup script for WebIntel Analytics
"""
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    
    print("🚀 Starting WebIntel Analytics Backend Server...")
    print("📍 API will be available at: http://localhost:8000")
    print("📖 API docs will be available at: http://localhost:8000/docs")
    print("🔧 Make sure your .env file contains GROQ_API_KEY")
    print()
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
