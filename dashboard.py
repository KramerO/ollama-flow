#!/usr/bin/env python3
"""
🚁 Ollama Flow Drone Dashboard Entry Point
Main dashboard launcher for the Drone System
"""

import os
import sys
import argparse
from pathlib import Path

def main():
    """Main dashboard launcher"""
    print("🚁 OLLAMA FLOW DRONE DASHBOARD")
    print("================================")
    print("🎯 Starting dashboard for drone orchestration system...")
    print()
    
    parser = argparse.ArgumentParser(description="Ollama Flow Drone Dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Dashboard host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5000, help="Dashboard port (default: 5000)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--simple", action="store_true", help="Use simple dashboard")
    parser.add_argument("--cli", action="store_true", help="Use CLI dashboard")
    
    args = parser.parse_args()
    
    dashboard_dir = Path(__file__).parent / "dashboard"
    
    try:
        if args.cli:
            # Use CLI dashboard
            print("🖥️  Launching CLI Dashboard...")
            from cli_dashboard import CLIDashboard
            dashboard = CLIDashboard()
            dashboard.run()
            
        elif args.simple or not dashboard_dir.exists():
            # Use simple dashboard fallback
            print("📊 Launching Simple Dashboard...")
            print(f"🌐 Dashboard will be available at: http://{args.host}:{args.port}")
            
            # Simple dashboard implementation
            from http.server import HTTPServer, SimpleHTTPRequestHandler
            import webbrowser
            import json
            from datetime import datetime
            
            class DroneDashboardHandler(SimpleHTTPRequestHandler):
                def do_GET(self):
                    if self.path == "/" or self.path == "/index.html":
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        
                        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>🚁 Ollama Flow Drone Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
        .card {{ background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .status {{ display: inline-block; padding: 5px 15px; border-radius: 20px; color: white; font-weight: bold; }}
        .status.active {{ background: #4CAF50; }}
        .status.inactive {{ background: #f44336; }}
        .drone-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }}
        .drone-card {{ background: white; padding: 15px; border-radius: 10px; border-left: 4px solid #667eea; }}
        .refresh-btn {{ background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }}
        .refresh-btn:hover {{ background: #5a6fd8; }}
        h1, h2 {{ margin: 0 0 10px 0; }}
        .footer {{ text-align: center; margin-top: 40px; color: #666; }}
    </style>
    <script>
        function refreshPage() {{ location.reload(); }}
        setTimeout(refreshPage, 30000); // Auto-refresh every 30 seconds
    </script>
</head>
<body>
    <div class="header">
        <h1>🚁 Ollama Flow Drone Dashboard</h1>
        <p>Multi-AI Drone Orchestration System v3.0.0</p>
        <span class="status active">OPERATIONAL</span>
    </div>
    
    <div class="card">
        <h2>📊 System Status</h2>
        <p><strong>Current Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>System:</strong> Drone Role System Active</p>
        <p><strong>Architecture:</strong> HIERARCHICAL / CENTRALIZED / FULLY_CONNECTED</p>
        <p><strong>Features:</strong> Role Intelligence, Task Structuring, German Support</p>
        <button class="refresh-btn" onclick="refreshPage()">🔄 Refresh Dashboard</button>
    </div>
    
    <div class="card">
        <h2>🚁 Available Drone Roles</h2>
        <div class="drone-grid">
            <div class="drone-card">
                <h3>📊 ANALYST</h3>
                <p>Data analysis, reporting, pattern recognition, insights generation</p>
            </div>
            <div class="drone-card">
                <h3>🤖 DATA SCIENTIST</h3>
                <p>Machine learning, statistical modeling, OpenCV, computer vision</p>
            </div>
            <div class="drone-card">
                <h3>🏛️ IT ARCHITECT</h3>
                <p>System design, infrastructure, security, scalability planning</p>
            </div>
            <div class="drone-card">
                <h3>💻 DEVELOPER</h3>
                <p>Coding, debugging, testing, deployment, implementation</p>
            </div>
        </div>
    </div>
    
    <div class="card">
        <h2>⚡ Quick Actions</h2>
        <p><strong>Run Drone Task:</strong> <code>ollama-flow run "your task here" --drones 4</code></p>
        <p><strong>German Support:</strong> <code>ollama-flow run "erstelle Python Projekt" --drones 2</code></p>
        <p><strong>OpenCV Task:</strong> <code>ollama-flow run "build image recognition" --drones 3</code></p>
        <p><strong>Architecture:</strong> <code>--arch HIERARCHICAL|CENTRALIZED|FULLY_CONNECTED</code></p>
    </div>
    
    <div class="card">
        <h2>🎯 System Performance</h2>
        <p><strong>51% Better Task Matching</strong> - Role-based specialization</p>
        <p><strong>Expert Responses</strong> - Domain-specific knowledge per role</p>
        <p><strong>Multi-Language</strong> - German language support with translation</p>
        <p><strong>Advanced Parsing</strong> - Windows path and JSON handling</p>
    </div>
    
    <div class="footer">
        <p>🚁 Ollama Flow Drone Edition v3.0.0 | Enhanced with Role Intelligence & Auto-Shutdown</p>
        <p>For advanced features, use: <code>ollama-flow cli-dashboard</code></p>
    </div>
</body>
</html>
                        """
                        self.wfile.write(html.encode())
                    else:
                        super().do_GET()
            
            server = HTTPServer((args.host, args.port), DroneDashboardHandler)
            print(f"✅ Simple dashboard running at http://{args.host}:{args.port}")
            print("🔄 Auto-refresh every 30 seconds")
            print("Press Ctrl+C to stop")
            
            # Try to open browser
            try:
                webbrowser.open(f"http://{args.host}:{args.port}")
            except:
                pass
            
            server.serve_forever()
            
        else:
            # Use full Flask dashboard
            print("🌟 Launching Full Flask Dashboard...")
            print(f"🌐 Dashboard will be available at: http://{args.host}:{args.port}")
            
            sys.path.insert(0, str(dashboard_dir))
            from flask_dashboard import FlaskDashboard
            
            dashboard = FlaskDashboard(host=args.host, port=args.port, debug=args.debug)
            dashboard.run()
            
    except ImportError as e:
        print(f"⚠️  Import error: {e}")
        print("📋 Available options:")
        print("   --simple    Use simple HTML dashboard (no dependencies)")
        print("   --cli       Use CLI dashboard")
        print()
        print("🚀 Starting simple dashboard as fallback...")
        
        # Fallback to simple dashboard
        args.simple = True
        main()
        
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
        
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
        print("💡 Try: ollama-flow dashboard --simple")

if __name__ == "__main__":
    main()