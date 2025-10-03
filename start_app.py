#!/usr/bin/env python3
"""
Main startup script for WebIntel Analytics
Starts both backend and frontend services
"""
import subprocess
import sys
import time
import os
import requests
from pathlib import Path

def check_backend():
    """Check if backend is running"""
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        return response.status_code == 200
    except:
        return False

def start_backend():
    """Start the backend server"""
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("❌ Backend directory not found!")
        return None
    
    print("🚀 Starting backend server...")
    process = subprocess.Popen([
        sys.executable, "start_backend.py"
    ], cwd=backend_dir)
    
    # Wait for backend to start
    for i in range(30):  # Wait up to 30 seconds
        if check_backend():
            print("✅ Backend server is running!")
            return process
        time.sleep(1)
        print(f"⏳ Waiting for backend... ({i+1}/30)")
    
    print("❌ Backend failed to start within 30 seconds")
    return process

def start_frontend():
    """Start the frontend server"""
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found!")
        return None
    
    print("🌐 Starting frontend server...")
    process = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", "ui_app.py",
        "--server.port", "8501",
        "--server.address", "localhost"
    ], cwd=frontend_dir)
    
    return process

def main():
    print("🌐 WebIntel Analytics - Full Stack Startup")
    print("=" * 50)
    
    # Check if .env exists
    if not Path(".env").exists():
        print("⚠️  .env file not found!")
        print("📋 Please create .env with your GROQ_API_KEY")
        print("Example:")
        print("GROQ_API_KEY=your_key_here")
        print("GROQ_MODEL=llama-3.1-70b-versatile")
        print()
    
    try:
        # Start backend
        backend_process = start_backend()
        if not backend_process:
            return 1
        
        time.sleep(2)  # Give backend a moment
        
        # Start frontend
        frontend_process = start_frontend()
        if not frontend_process:
            backend_process.terminate()
            return 1
        
        print()
        print("🎉 Both services are starting!")
        print("📍 Frontend: http://localhost:8501")
        print("📍 Backend API: http://localhost:8000")
        print("📖 API Docs: http://localhost:8000/docs")
        print()
        print("Press Ctrl+C to stop both services")
        
        # Wait for both processes
        try:
            backend_process.wait()
            frontend_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down services...")
            backend_process.terminate()
            frontend_process.terminate()
            
            # Wait for graceful shutdown
            time.sleep(2)
            
            # Force kill if needed
            try:
                backend_process.kill()
                frontend_process.kill()
            except:
                pass
            
            print("✅ Services stopped")
            return 0
            
    except Exception as e:
        print(f"❌ Error starting services: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
