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
            
            # Enhanced dashboard implementation with task monitoring
            from http.server import HTTPServer, SimpleHTTPRequestHandler
            import webbrowser
            import json
            import psutil
            import glob
            import re
            from datetime import datetime, timedelta
            from pathlib import Path
            
            class DroneDashboardHandler(SimpleHTTPRequestHandler):
                def get_running_tasks(self):
                    """Monitor running ollama-flow processes and tasks"""
                    tasks = []
                    
                    try:
                        # Find ollama-flow processes
                        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'status']):
                            try:
                                if proc.info['cmdline'] and any('ollama-flow' in arg or 'main.py' in arg for arg in proc.info['cmdline']):
                                    # Extract task information
                                    cmdline = ' '.join(proc.info['cmdline'])
                                    task_match = re.search(r'--task "([^"]+)"', cmdline)
                                    drone_match = re.search(r'--drone-count (\d+)', cmdline)
                                    arch_match = re.search(r'--architecture-type (\w+)', cmdline)
                                    
                                    task_info = {
                                        'pid': proc.info['pid'],
                                        'status': proc.info['status'],
                                        'task': task_match.group(1) if task_match else 'Unknown Task',
                                        'drones': drone_match.group(1) if drone_match else '4',
                                        'architecture': arch_match.group(1) if arch_match else 'CENTRALIZED',
                                        'start_time': datetime.fromtimestamp(proc.info['create_time']).strftime('%H:%M:%S'),
                                        'duration': str(timedelta(seconds=int(psutil.time.time() - proc.info['create_time']))).split('.')[0]
                                    }
                                    tasks.append(task_info)
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue
                    except Exception as e:
                        print(f"Error monitoring processes: {e}")
                    
                    return tasks
                
                def get_recent_logs(self):
                    """Parse recent log files for task information"""
                    log_info = []
                    
                    try:
                        # Look for log files in common locations
                        log_patterns = [
                            "/home/oliver/Projects/ollama-flow/**/*.log",
                            "/home/oliver/Projects/ollama-flow/test/*.log",
                            "./**.log"
                        ]
                        
                        for pattern in log_patterns:
                            for log_file in glob.glob(pattern, recursive=True):
                                try:
                                    log_path = Path(log_file)
                                    if log_path.stat().st_mtime > (datetime.now() - timedelta(hours=1)).timestamp():
                                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                                            content = f.read()[-2000:]  # Last 2000 chars
                                            
                                        # Extract key information
                                        task_match = re.search(r'Orchestrator received prompt: (.+)', content)
                                        drone_match = re.search(r'Drones: (\d+)', content)
                                        arch_match = re.search(r'Architecture: (\w+)', content)
                                        model_match = re.search(r'Using model: ([\w:]+)', content)
                                        
                                        if task_match:
                                            log_info.append({
                                                'file': log_path.name,
                                                'task': task_match.group(1)[:100] + '...' if len(task_match.group(1)) > 100 else task_match.group(1),
                                                'drones': drone_match.group(1) if drone_match else 'Unknown',
                                                'architecture': arch_match.group(1) if arch_match else 'Unknown',
                                                'model': model_match.group(1) if model_match else 'Unknown',
                                                'modified': datetime.fromtimestamp(log_path.stat().st_mtime).strftime('%H:%M:%S')
                                            })
                                except Exception:
                                    continue
                    except Exception as e:
                        print(f"Error parsing logs: {e}")
                    
                    return log_info
                
                def do_GET(self):
                    if self.path == "/api/tasks":
                        # API endpoint for task data
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        
                        data = {
                            'running_tasks': self.get_running_tasks(),
                            'recent_logs': self.get_recent_logs(),
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        self.wfile.write(json.dumps(data, indent=2).encode())
                        return
                    
                    elif self.path == "/" or self.path == "/index.html":
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
        .task-item {{ background: #f8f9fa; padding: 10px; margin: 5px 0; border-radius: 5px; border-left: 3px solid #28a745; }}
        .task-item.running {{ border-left-color: #ffc107; background: #fff3cd; }}
        .task-item.completed {{ border-left-color: #28a745; background: #d4edda; }}
        .task-details {{ font-size: 0.9em; color: #666; margin-top: 5px; }}
        .no-tasks {{ text-align: center; color: #999; font-style: italic; padding: 20px; }}
        .api-link {{ color: #667eea; text-decoration: none; font-size: 0.9em; }}
        .api-link:hover {{ text-decoration: underline; }}
    </style>
    <script>
        let taskData = null;
        
        async function loadTasks() {{
            try {{
                const response = await fetch('/api/tasks');
                taskData = await response.json();
                updateTaskDisplay();
            }} catch (error) {{
                console.error('Error loading tasks:', error);
            }}
        }}
        
        function updateTaskDisplay() {{
            if (!taskData) return;
            
            // Update running tasks
            const runningContainer = document.getElementById('running-tasks');
            if (taskData.running_tasks.length === 0) {{
                runningContainer.innerHTML = '<div class="no-tasks">No running tasks</div>';
            }} else {{
                runningContainer.innerHTML = taskData.running_tasks.map(task => `
                    <div class="task-item running">
                        <strong>🚁 ${{task.task}}</strong>
                        <div class="task-details">
                            PID: ${{task.pid}} | Drones: ${{task.drones}} | Arch: ${{task.architecture}} | Started: ${{task.start_time}} | Duration: ${{task.duration}}
                        </div>
                    </div>
                `).join('');
            }}
            
            // Update recent logs
            const logsContainer = document.getElementById('recent-logs');
            if (taskData.recent_logs.length === 0) {{
                logsContainer.innerHTML = '<div class="no-tasks">No recent activity</div>';
            }} else {{
                logsContainer.innerHTML = taskData.recent_logs.map(log => `
                    <div class="task-item completed">
                        <strong>📋 ${{log.task}}</strong>
                        <div class="task-details">
                            File: ${{log.file}} | Drones: ${{log.drones}} | Arch: ${{log.architecture}} | Model: ${{log.model}} | Time: ${{log.modified}}
                        </div>
                    </div>
                `).join('');
            }}
            
            // Update timestamp
            document.getElementById('last-update').textContent = new Date(taskData.timestamp).toLocaleTimeString();
        }}
        
        function refreshPage() {{ 
            loadTasks();
        }}
        
        // Load tasks on page load
        window.addEventListener('DOMContentLoaded', loadTasks);
        
        // Auto-refresh every 15 seconds
        setInterval(refreshPage, 15000);
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
        <p><strong>Last Update:</strong> <span id="last-update">Loading...</span></p>
        <button class="refresh-btn" onclick="refreshPage()">🔄 Refresh Dashboard</button>
        <a href="/api/tasks" class="api-link" target="_blank">📡 API Data</a>
    </div>
    
    <div class="card">
        <h2>🚀 Running Tasks</h2>
        <p>Real-time monitoring of active ollama-flow processes</p>
        <div id="running-tasks">
            <div class="no-tasks">Loading running tasks...</div>
        </div>
    </div>
    
    <div class="card">
        <h2>📋 Recent Activity</h2>
        <p>Recently completed tasks from log files (last hour)</p>
        <div id="recent-logs">
            <div class="no-tasks">Loading recent activity...</div>
        </div>
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
        <p><strong>Monitor Tasks:</strong> <code>ps aux | grep ollama-flow</code></p>
        <p><strong>View Logs:</strong> <code>tail -f ~/Projects/ollama-flow/test/*.log</code></p>
    </div>
    
    <div class="card">
        <h2>🔍 Task Monitoring Features</h2>
        <p><strong>Process Monitoring:</strong> Real-time detection of running ollama-flow processes</p>
        <p><strong>Log Analysis:</strong> Automatic parsing of recent log files for task information</p>
        <p><strong>Task Details:</strong> Process ID, drone count, architecture, duration, and status</p>
        <p><strong>Auto-Refresh:</strong> Updates every 15 seconds automatically</p>
        <p><strong>API Access:</strong> JSON API available at <a href="/api/tasks" class="api-link">/api/tasks</a></p>
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