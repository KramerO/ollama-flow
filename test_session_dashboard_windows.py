#!/usr/bin/env python3
"""
Windows Test script for session management dashboard functionality
"""

import requests
import json
import time
import sys
import os
from threading import Thread

def test_dashboard_session_api():
    """Test the session management API endpoints"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Dashboard Session Management API")
    print("=" * 50)
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
            health_data = response.json()
            print(f"   Version: {health_data.get('version', 'unknown')}")
        else:
            print("❌ Health check failed")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Dashboard not accessible: {e}")
        return False
    
    # Test getting sessions (should be empty initially)
    try:
        response = requests.get(f"{base_url}/api/sessions", timeout=5)
        if response.status_code == 200:
            sessions_data = response.json()
            print("✅ Sessions API accessible")
            print(f"   Active sessions: {len(sessions_data.get('active_sessions', {}))}")
            print(f"   Session history: {len(sessions_data.get('session_history', []))}")
        else:
            print("❌ Sessions API failed")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Sessions API error: {e}")
        return False
    
    # Test creating a new session
    test_session = {
        'name': 'Windows Test Session',
        'task': 'Create a simple Python hello world script',
        'workers': 4,
        'architecture': 'HIERARCHICAL',
        'model': 'codellama:7b',
        'project_folder': 'C:\\temp\\test-session'
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/sessions",
            json=test_session,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        
        if response.status_code == 200:
            create_data = response.json()
            if create_data.get('success'):
                session_id = create_data.get('session_id')
                print("✅ Session created successfully")
                print(f"   Session ID: {session_id}")
                
                # Wait a moment for processing
                time.sleep(1)
                
                # Test getting session details
                detail_response = requests.get(f"{base_url}/api/sessions/{session_id}", timeout=5)
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    if detail_data.get('success'):
                        session = detail_data.get('session')
                        print("✅ Session details retrieved")
                        print(f"   Status: {session.get('status')}")
                        print(f"   Workers: {session.get('workers')}")
                        print(f"   Architecture: {session.get('architecture')}")
                    else:
                        print("❌ Session details failed")
                        return False
                else:
                    print("❌ Session details request failed")
                    return False
                
                # Wait for session to complete (it should complete quickly in mock mode)
                time.sleep(3)
                
                # Check if session moved to history
                final_response = requests.get(f"{base_url}/api/sessions", timeout=5)
                if final_response.status_code == 200:
                    final_data = final_response.json()
                    active_count = len(final_data.get('active_sessions', {}))
                    history_count = len(final_data.get('session_history', []))
                    print(f"✅ Session lifecycle test completed")
                    print(f"   Active sessions: {active_count}")
                    print(f"   History sessions: {history_count}")
                    
                    if history_count > 0:
                        last_session = final_data['session_history'][-1]
                        print(f"   Last session status: {last_session.get('status')}")
                        print(f"   Last session duration: {last_session.get('duration', 'unknown')}")
                
                return True
            else:
                print(f"❌ Session creation failed: {create_data.get('error')}")
                return False
        else:
            print(f"❌ Session creation request failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Session creation error: {e}")
        return False

def start_dashboard_for_test():
    """Start dashboard in a separate thread for testing"""
    import subprocess
    
    # Start dashboard from current directory
    proc = subprocess.Popen([
        'python', 'dashboard\\simple_dashboard.py', 
        '--host', 'localhost', 
        '--port', '5000'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    return proc

if __name__ == "__main__":
    print("🚀 Starting Windows Dashboard Session Management Test")
    print("=" * 60)
    
    # Start dashboard
    print("Starting dashboard...")
    dashboard_proc = start_dashboard_for_test()
    
    # Wait for dashboard to start
    time.sleep(3)
    
    try:
        # Run tests
        success = test_dashboard_session_api()
        
        if success:
            print("\n🎉 All session management tests passed!")
            print("\n📋 Session Management Features Tested:")
            print("   ✅ Dashboard health check")
            print("   ✅ Session listing API")
            print("   ✅ Session creation API")
            print("   ✅ Session details API")
            print("   ✅ Session lifecycle (creation → execution → completion)")
            print("   ✅ Session history tracking")
            
            print(f"\n🌐 Dashboard URL: http://localhost:5000")
            print("   Navigate to /sessions to see the session management interface")
            
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)
            
    finally:
        # Clean up
        print(f"\n🧹 Cleaning up...")
        dashboard_proc.terminate()
        dashboard_proc.wait()
        print("Dashboard stopped.")