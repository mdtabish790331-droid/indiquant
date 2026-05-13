import subprocess
import sys
import os

def run_services():
    print("🚀 Starting IndiQuant Services...")
    
    # Auth Service
    auth_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--port", "8001", "--reload"],
        cwd=os.path.join(os.getcwd(), "auth_service"),
        shell=True
    )
    
    # Backend Service
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--port", "8002", "--reload"],
        cwd=os.path.join(os.getcwd(), "backend_service"),
        shell=True
    )
    
    print("✅ Auth Service running on http://localhost:8001")
    print("✅ Backend Service running on http://localhost:8002")
    print("\n📋 API Endpoints:")
    print("   POST   /api/auth/register  - Register user")
    print("   POST   /api/auth/login     - Login user")
    print("   GET    /api/auth/me        - Get profile")
    print("   POST   /api/tournaments/   - Create tournament")
    print("   GET    /api/tournaments/   - List tournaments")
    print("   POST   /api/submissions/{id} - Submit predictions")
    
    print("\n⚠️ Press Ctrl+C to stop all services")
    
    try:
        auth_process.wait()
        backend_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        auth_process.terminate()
        backend_process.terminate()

if __name__ == "__main__":
    run_services()