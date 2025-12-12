#!/usr/bin/env python3
"""
Script to start all OAuth2 system components:
1. Authorization Server (Omar) - port 3000
2. Resource Server (Your API) - port 5000
3. Frontend Server (Dashboard) - port 8080
"""

import subprocess
import sys
import time
import os

def main():
    print("🚀 Starting OAuth2 System...")
    print("=" * 50)
    
    # Change to project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    # Start Authorization Server (Omar) on port 3000
    print("1️⃣  Starting Authorization Server (Omar)...")
    auth_server = subprocess.Popen([
        sys.executable, "auth_server.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    time.sleep(2)  # Give it time to start
    
    # Start Resource Server (Your API) on port 5000
    print("2️⃣  Starting Resource Server (Your API)...")
    resource_server = subprocess.Popen([
        sys.executable, "app.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    time.sleep(2)  # Give it time to start
    
    # Start Frontend Server (Dashboard) on port 8080
    print("3️⃣  Starting Frontend Server (Dashboard)...")
    frontend_server = subprocess.Popen([
        sys.executable, "frontend/server.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    time.sleep(2)  # Give it time to start
    
    print("\n" + "=" * 50)
    print("✅ All servers started successfully!")
    print("\n🔗 Access the system at:")
    print("   🔐 Authorization Server: http://localhost:3000")
    print("   🛡️  Resource Server:     http://localhost:5000")
    print("   📱 Frontend Dashboard:   http://localhost:8080")
    print("\n🛑 Press Ctrl+C to stop all servers")
    print("=" * 50)
    
    try:
        # Wait for all processes
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping all servers...")
        auth_server.terminate()
        resource_server.terminate()
        frontend_server.terminate()
        print("✅ All servers stopped.")
        sys.exit(0)

if __name__ == "__main__":
    main()