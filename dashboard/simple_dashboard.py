#!/usr/bin/env python3
"""
Simple Flask Web Dashboard for Enhanced Ollama Flow Framework
Simplified version without async complications
"""

import os
import sys
import json
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Flask, render_template, jsonify, request
import psutil

# Try to import SocketIO, fallback if not available
try:
    from flask_socketio import SocketIO, emit
    HAS_SOCKETIO = True
except ImportError:
    HAS_SOCKETIO = False
    SocketIO = None

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
logger = logging.getLogger(__name__)

class SimpleDashboard:
    """Simple Flask web dashboard for Ollama Flow Framework"""
    
    def __init__(self, host='localhost', port=5000, debug=False):
        """Initialize simple dashboard"""
        self.host = host
        self.port = port
        self.debug = debug
        
        # Flask app setup
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'ollama-flow-dashboard-secret'
        
        # Setup SocketIO if available
        if HAS_SOCKETIO:
            self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        else:
            self.socketio = None
        
        # Dashboard state
        self.is_running = False
        self.current_task = None
        self.task_history = []
        self.system_metrics = {}
        self.update_thread = None
        
        # Session management
        self.active_sessions = {}
        self.session_history = []
        
        # Setup routes
        self._setup_routes()
        
        # Setup SocketIO events if available
        if HAS_SOCKETIO:
            self._setup_socketio_events()
    
    def _render_page(self, title, content):
        """Render a page with common layout"""
        return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Ollama Flow - {title}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f5f5f5; }}
                    .header {{ background: #343a40; color: white; padding: 1rem 0; }}
                    .header .container {{ max-width: 1200px; margin: 0 auto; padding: 0 20px; }}
                    .nav {{ margin-top: 10px; }}
                    .nav a {{ color: #adb5bd; text-decoration: none; margin-right: 20px; padding: 5px 10px; border-radius: 4px; }}
                    .nav a:hover, .nav a.active {{ background: #495057; color: white; }}
                    .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
                    .card {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                    .metric {{ display: inline-block; margin: 10px 20px; }}
                    .status {{ color: #28a745; font-weight: bold; }}
                    .error {{ color: #dc3545; }}
                    .warning {{ color: #ffc107; }}
                    h1 {{ color: #333; margin: 0; }}
                    h2 {{ color: #666; }}
                    .btn {{ padding: 8px 16px; margin: 5px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; }}
                    .btn-primary {{ background: #007bff; color: white; }}
                    .btn-success {{ background: #28a745; color: white; }}
                    .btn-danger {{ background: #dc3545; color: white; }}
                    .btn-secondary {{ background: #6c757d; color: white; }}
                    .btn-sm {{ padding: 4px 8px; font-size: 0.875rem; }}
                    .btn:hover {{ opacity: 0.8; }}
                    .btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}
                    .form-group {{ margin: 15px 0; }}
                    .form-group label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
                    .form-group input, .form-group select, .form-group textarea {{ width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }}
                    .form-group textarea {{ height: 100px; resize: vertical; }}
                    .session-item {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 4px; }}
                    .session-item.running {{ border-color: #28a745; background: #f8fff9; }}
                    .session-item.stopped {{ border-color: #6c757d; background: #f8f9fa; }}
                    .session-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
                    .session-meta {{ font-size: 0.9em; color: #666; }}
                    .two-column {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
                    @media (max-width: 768px) {{ .two-column {{ grid-template-columns: 1fr; }} }}
                </style>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
            </head>
            <body>
                <div class="header">
                    <div class="container">
                        <h1>🚀 Ollama Flow Dashboard</h1>
                        <div class="nav">
                            <a href="/" class="{'active' if title == 'System Dashboard' else ''}">System Overview</a>
                            <a href="/sessions" class="{'active' if title == 'Session Management' else ''}">Sessions</a>
                        </div>
                    </div>
                </div>
                <div class="container">
                    {content}
                </div>
                <script>
                    // Common JavaScript functions
                    const socket = typeof io !== 'undefined' ? io() : null;
                    
                    if (socket) {{
                        socket.on('connect', function() {{
                            console.log('Connected to dashboard');
                        }});
                        
                        socket.on('system_update', function(data) {{
                            updateSystemStatus(data);
                        }});
                    }}
                    
                    function updateSystemStatus(data) {{
                        if (data.system && document.getElementById('status')) {{
                            document.getElementById('status').textContent = data.system.running ? 'Running' : 'Stopped';
                            if (document.getElementById('timestamp')) {{
                                document.getElementById('timestamp').textContent = 'Last updated: ' + data.system.timestamp;
                            }}
                        }}
                        if (data.resources) {{
                            if (document.getElementById('cpu')) document.getElementById('cpu').textContent = data.resources.cpu_percent.toFixed(1);
                            if (document.getElementById('memory')) document.getElementById('memory').textContent = data.resources.memory_percent.toFixed(1);
                            if (document.getElementById('disk')) document.getElementById('disk').textContent = data.resources.disk_percent.toFixed(1);
                        }}
                    }}
                    
                    function refreshStatus() {{
                        fetch('/api/status')
                            .then(response => response.json())
                            .then(data => updateSystemStatus(data))
                            .catch(error => console.error('Error:', error));
                    }}
                    
                    // Auto-refresh every 5 seconds
                    setInterval(refreshStatus, 5000);
                    
                    // Initialize
                    refreshStatus();
                </script>
            </body>
            </html>
            """
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main dashboard page"""
            return self._render_page("System Dashboard", self._get_dashboard_content())
        
        @self.app.route('/sessions')
        def sessions():
            """Sessions management page"""
            return self._render_page("Session Management", self._get_sessions_content())
        
        @self.app.route('/api/status')
        def api_status():
            """Get system status"""
            try:
                status = {
                    'system': {
                        'running': self.is_running,
                        'current_task': self.current_task,
                        'timestamp': datetime.now().isoformat()
                    },
                    'resources': {
                        'cpu_percent': psutil.cpu_percent(interval=0.1),
                        'memory_percent': psutil.virtual_memory().percent,
                        'disk_percent': psutil.disk_usage('/').percent,
                        'processes': len(psutil.pids())
                    }
                }
                
                return jsonify(status)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/health')
        def api_health():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '2.0.0'
            })
        
        @self.app.route('/api/sessions', methods=['GET', 'POST'])
        def api_sessions():
            """Manage sessions"""
            if request.method == 'GET':
                return jsonify({
                    'success': True,
                    'active_sessions': self.active_sessions,
                    'session_history': self.session_history
                })
            
            elif request.method == 'POST':
                try:
                    data = request.get_json()
                    session_id = f"session_{int(time.time())}"
                    
                    # Create new session
                    session = {
                        'id': session_id,
                        'name': data.get('name', 'Untitled Session'),
                        'task': data.get('task', ''),
                        'workers': data.get('workers', 4),
                        'architecture': data.get('architecture', 'HIERARCHICAL'),
                        'model': data.get('model', 'codellama:7b'),
                        'project_folder': data.get('project_folder', None),
                        'status': 'running',
                        'started_at': datetime.now().isoformat(),
                        'created_by': 'dashboard'
                    }
                    
                    # Add to active sessions
                    self.active_sessions[session_id] = session
                    
                    # Start session (mock implementation - would integrate with actual framework)
                    self._start_session_background(session)
                    
                    return jsonify({
                        'success': True,
                        'session_id': session_id,
                        'message': 'Session created and started successfully'
                    })
                    
                except Exception as e:
                    return jsonify({
                        'success': False,
                        'error': str(e)
                    }), 400
        
        @self.app.route('/api/sessions/<session_id>')
        def api_session_details(session_id):
            """Get session details"""
            if session_id in self.active_sessions:
                return jsonify({
                    'success': True,
                    'session': self.active_sessions[session_id]
                })
            else:
                # Look in history
                for session in self.session_history:
                    if session.get('id') == session_id:
                        return jsonify({
                            'success': True,
                            'session': session
                        })
                
                return jsonify({
                    'success': False,
                    'error': 'Session not found'
                }), 404
        
        @self.app.route('/api/sessions/<session_id>/stop', methods=['POST'])
        def api_stop_session(session_id):
            """Stop a running session"""
            if session_id in self.active_sessions:
                try:
                    session = self.active_sessions[session_id]
                    session['status'] = 'stopped'
                    session['stopped_at'] = datetime.now().isoformat()
                    
                    # Calculate duration
                    if 'started_at' in session:
                        start_time = datetime.fromisoformat(session['started_at'])
                        duration = datetime.now() - start_time
                        session['duration'] = f"{duration.seconds // 60}m {duration.seconds % 60}s"
                    
                    # Move to history
                    self.session_history.append(session.copy())
                    del self.active_sessions[session_id]
                    
                    return jsonify({
                        'success': True,
                        'message': 'Session stopped successfully'
                    })
                    
                except Exception as e:
                    return jsonify({
                        'success': False,
                        'error': str(e)
                    }), 500
            else:
                return jsonify({
                    'success': False,
                    'error': 'Session not found or already stopped'
                }), 404
        
    def _get_dashboard_content(self):
            """Get dashboard content"""
            return """
                    <div class="card">
                        <h2>System Status</h2>
                        <div id="status" class="status">Loading...</div>
                        <div id="timestamp"></div>
                    </div>
                    
                    <div class="card">
                        <h2>System Resources</h2>
                        <div class="metric">CPU: <span id="cpu">-</span>%</div>
                        <div class="metric">Memory: <span id="memory">-</span>%</div>
                        <div class="metric">Disk: <span id="disk">-</span>%</div>
                    </div>
                    
                    <div class="card">
                        <h2>Quick Actions</h2>
                        <button onclick="refreshStatus()" class="btn btn-primary">Refresh Status</button>
                        <button onclick="viewLogs()" class="btn btn-secondary">View Logs</button>
                        <a href="/sessions" class="btn btn-success">Manage Sessions</a>
                    </div>
                    
                    <div class="card">
                        <h2>Recent Tasks</h2>
                        <div id="tasks">No tasks executed yet.</div>
                    </div>
                    
                    <script>
                        function viewLogs() {
                            alert('Logs feature coming soon!');
                        }
                    </script>
            """
        
        def _get_sessions_content(self):
            """Get sessions management content"""
            active_sessions_html = ""
            if self.active_sessions:
                for session_id, session in self.active_sessions.items():
                    status_class = "running" if session.get('status') == 'running' else "stopped"
                    active_sessions_html += f"""
                        <div class="session-item {status_class}">
                            <div class="session-header">
                                <h4>{session.get('name', session_id)}</h4>
                                <div>
                                    <button onclick="stopSession('{session_id}')" class="btn btn-danger btn-sm">Stop</button>
                                    <button onclick="viewSession('{session_id}')" class="btn btn-secondary btn-sm">View</button>
                                </div>
                            </div>
                            <div class="session-meta">
                                Status: {session.get('status', 'unknown')} | 
                                Workers: {session.get('workers', 0)} | 
                                Architecture: {session.get('architecture', 'unknown')} |
                                Started: {session.get('started_at', 'unknown')}
                            </div>
                            <div style="margin-top: 8px; font-size: 0.9em;">
                                Task: {session.get('task', 'No description')[:100]}...
                            </div>
                        </div>
                    """
            else:
                active_sessions_html = "<p>No active sessions</p>"
            
            history_html = ""
            if self.session_history:
                for session in self.session_history[-5:]:  # Show last 5
                    history_html += f"""
                        <div class="session-item stopped">
                            <div class="session-header">
                                <h4>{session.get('name', session.get('id', 'Unknown'))}</h4>
                                <span class="session-meta">Completed</span>
                            </div>
                            <div class="session-meta">
                                Duration: {session.get('duration', 'unknown')} | 
                                Workers: {session.get('workers', 0)} | 
                                Architecture: {session.get('architecture', 'unknown')}
                            </div>
                        </div>
                    """
            else:
                history_html = "<p>No session history</p>"
            
            return f"""
                    <div class="two-column">
                        <div>
                            <div class="card">
                                <h2>Active Sessions</h2>
                                <div id="active-sessions">
                                    {active_sessions_html}
                                </div>
                            </div>
                            
                            <div class="card">
                                <h2>Session History</h2>
                                <div id="session-history">
                                    {history_html}
                                </div>
                            </div>
                        </div>
                        
                        <div>
                            <div class="card">
                                <h2>Create New Session</h2>
                                <form id="new-session-form" onsubmit="createSession(event)">
                                    <div class="form-group">
                                        <label for="session-name">Session Name:</label>
                                        <input type="text" id="session-name" name="name" required placeholder="My Task Session">
                                    </div>
                                    
                                    <div class="form-group">
                                        <label for="task-description">Task Description:</label>
                                        <textarea id="task-description" name="task" required placeholder="Describe what you want the agents to accomplish..."></textarea>
                                    </div>
                                    
                                    <div class="form-group">
                                        <label for="workers">Number of Workers:</label>
                                        <select id="workers" name="workers">
                                            <option value="2">2 Workers</option>
                                            <option value="4" selected>4 Workers</option>
                                            <option value="6">6 Workers</option>
                                            <option value="8">8 Workers</option>
                                            <option value="12">12 Workers</option>
                                        </select>
                                    </div>
                                    
                                    <div class="form-group">
                                        <label for="architecture">Architecture:</label>
                                        <select id="architecture" name="architecture">
                                            <option value="HIERARCHICAL" selected>Hierarchical</option>
                                            <option value="CENTRALIZED">Centralized</option>
                                            <option value="FULLY_CONNECTED">Fully Connected</option>
                                        </select>
                                    </div>
                                    
                                    <div class="form-group">
                                        <label for="model">Model:</label>
                                        <select id="model" name="model">
                                            <option value="codellama:7b" selected>CodeLlama 7B</option>
                                            <option value="llama3">Llama3</option>
                                            <option value="codellama:13b">CodeLlama 13B</option>
                                            <option value="codellama:34b">CodeLlama 34B</option>
                                        </select>
                                    </div>
                                    
                                    <div class="form-group">
                                        <label for="project-folder">Project Folder (optional):</label>
                                        <input type="text" id="project-folder" name="project_folder" placeholder="/path/to/project">
                                    </div>
                                    
                                    <div class="form-group">
                                        <button type="submit" class="btn btn-success" style="width: 100%;">Create & Start Session</button>
                                    </div>
                                </form>
                            </div>
                            
                            <div class="card">
                                <h2>Session Statistics</h2>
                                <div class="metric">Total Sessions: <span id="total-sessions">{len(self.session_history)}</span></div>
                                <div class="metric">Active Sessions: <span id="active-count">{len(self.active_sessions)}</span></div>
                                <div class="metric">Avg Duration: <span id="avg-duration">-</span></div>
                            </div>
                        </div>
                    </div>
                    
                    <script>
                        function createSession(event) {{
                            event.preventDefault();
                            
                            const formData = new FormData(event.target);
                            const sessionData = {{
                                name: formData.get('name'),
                                task: formData.get('task'),
                                workers: parseInt(formData.get('workers')),
                                architecture: formData.get('architecture'),
                                model: formData.get('model'),
                                project_folder: formData.get('project_folder') || null
                            }};
                            
                            fetch('/api/sessions', {{
                                method: 'POST',
                                headers: {{
                                    'Content-Type': 'application/json',
                                }},
                                body: JSON.stringify(sessionData)
                            }})
                            .then(response => response.json())
                            .then(data => {{
                                if (data.success) {{
                                    alert('Session created successfully!');
                                    location.reload();
                                }} else {{
                                    alert('Error creating session: ' + data.error);
                                }}
                            }})
                            .catch(error => {{
                                console.error('Error:', error);
                                alert('Error creating session');
                            }});
                        }}
                        
                        function stopSession(sessionId) {{
                            if (confirm('Are you sure you want to stop this session?')) {{
                                fetch(`/api/sessions/${{sessionId}}/stop`, {{
                                    method: 'POST'
                                }})
                                .then(response => response.json())
                                .then(data => {{
                                    if (data.success) {{
                                        location.reload();
                                    }} else {{
                                        alert('Error stopping session: ' + data.error);
                                    }}
                                }})
                                .catch(error => {{
                                    console.error('Error:', error);
                                    alert('Error stopping session');
                                }});
                            }}
                        }}
                        
                        function viewSession(sessionId) {{
                            fetch(`/api/sessions/${{sessionId}}`)
                                .then(response => response.json())
                                .then(data => {{
                                    if (data.success) {{
                                        const session = data.session;
                                        alert(`Session Details:\\n\\nName: ${{session.name}}\\nStatus: ${{session.status}}\\nWorkers: ${{session.workers}}\\nArchitecture: ${{session.architecture}}\\nTask: ${{session.task}}`);
                                    }} else {{
                                        alert('Error loading session details');
                                    }}
                                }})
                                .catch(error => {{
                                    console.error('Error:', error);
                                    alert('Error loading session details');
                                }});
                        }}
                        
                        // Auto-refresh sessions every 10 seconds
                        setInterval(() => {{
                            if (window.location.pathname === '/sessions') {{
                                location.reload();
                            }}
                        }}, 10000);
                    </script>
            """
    
    def _setup_socketio_events(self):
        """Setup SocketIO events for real-time updates"""
        if not HAS_SOCKETIO or not self.socketio:
            return
            
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            logger.info("Client connected to dashboard")
            emit('status', {'message': 'Connected to Ollama Flow Dashboard'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            logger.info("Client disconnected from dashboard")
    
    def _emit_system_update(self):
        """Emit system status update via SocketIO"""
        if not HAS_SOCKETIO or not self.socketio:
            return
            
        try:
            status = {
                'system': {
                    'running': self.is_running,
                    'timestamp': datetime.now().isoformat()
                },
                'resources': {
                    'cpu_percent': psutil.cpu_percent(interval=0.1),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_percent': psutil.disk_usage('/').percent
                }
            }
            self.socketio.emit('system_update', status)
        except Exception as e:
            logger.error(f"Failed to emit system update: {e}")
    
    def _start_session_background(self, session):
        """Start session execution in background thread"""
        def run_session():
            try:
                session_id = session['id']
                logger.info(f"Starting session {session_id}: {session['name']}")
                
                # Mock session execution - in real implementation, this would:
                # 1. Import enhanced_main
                # 2. Create OllamaFlowFramework instance
                # 3. Run the task with specified parameters
                
                # Simulate work for demo
                import subprocess
                import shlex
                
                cmd_parts = [
                    'python3', 'enhanced_main.py',
                    '--task', session['task'],
                    '--workers', str(session['workers']),
                    '--arch', session['architecture'],
                    '--model', session['model']
                ]
                
                if session.get('project_folder'):
                    cmd_parts.extend(['--project-folder', session['project_folder']])
                
                # Update session status
                session['status'] = 'executing'
                session['command'] = ' '.join(cmd_parts)
                
                # In a real implementation, this would execute the command
                # For now, we'll simulate completion after a short delay
                time.sleep(2)
                
                # Simulate completion
                session['status'] = 'completed'
                session['completed_at'] = datetime.now().isoformat()
                
                # Calculate duration
                if 'started_at' in session:
                    start_time = datetime.fromisoformat(session['started_at'])
                    duration = datetime.now() - start_time
                    session['duration'] = f"{duration.seconds // 60}m {duration.seconds % 60}s"
                
                # Move to history
                self.session_history.append(session.copy())
                if session_id in self.active_sessions:
                    del self.active_sessions[session_id]
                
                logger.info(f"Session {session_id} completed successfully")
                
            except Exception as e:
                logger.error(f"Session {session_id} failed: {e}")
                session['status'] = 'failed'
                session['error'] = str(e)
                session['failed_at'] = datetime.now().isoformat()
                
                # Move to history even if failed
                self.session_history.append(session.copy())
                if session_id in self.active_sessions:
                    del self.active_sessions[session_id]
        
        # Start session in background thread
        session_thread = threading.Thread(target=run_session, daemon=True)
        session_thread.start()
    
    def start_update_thread(self):
        """Start background thread for periodic updates"""
        def update_loop():
            while True:
                try:
                    self._emit_system_update()
                    time.sleep(5)  # Update every 5 seconds
                except Exception as e:
                    logger.error(f"Update loop error: {e}")
                    time.sleep(5)
        
        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()
    
    def run(self):
        """Run the simple dashboard"""
        logger.info(f"Starting Simple Ollama Flow Dashboard on {self.host}:{self.port}")
        
        if self.debug:
            print(f"""
🚀 Simple Ollama Flow Dashboard Starting
========================================
URL: http://{self.host}:{self.port}
Mode: {'Debug' if self.debug else 'Production'}

Features:
✓ Real-time system monitoring
✓ Resource usage display
✓ Simple web interface
✓ WebSocket updates

Press Ctrl+C to stop
========================================
            """)
        
        # Start update thread
        self.start_update_thread()
        
        # Run Flask app
        if HAS_SOCKETIO and self.socketio:
            # Run with SocketIO
            self.socketio.run(
                self.app,
                host=self.host,
                port=self.port,
                debug=self.debug,
                use_reloader=False
            )
        else:
            # Run plain Flask
            self.app.run(
                host=self.host,
                port=self.port,
                debug=self.debug,
                use_reloader=False
            )

def main():
    """Main entry point for simple dashboard"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple Ollama Flow Dashboard')
    parser.add_argument('--host', default='localhost', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO if not args.debug else logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run simple dashboard
    dashboard = SimpleDashboard(
        host=args.host,
        port=args.port,
        debug=args.debug
    )
    
    try:
        dashboard.run()
    except KeyboardInterrupt:
        print("\n👋 Simple Dashboard stopped")
    except Exception as e:
        print(f"❌ Dashboard failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()