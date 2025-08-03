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
        
        # Setup routes
        self._setup_routes()
        
        # Setup SocketIO events if available
        if HAS_SOCKETIO:
            self._setup_socketio_events()
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main dashboard page"""
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Ollama Flow Dashboard</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                    .container {{ max-width: 1200px; margin: 0 auto; }}
                    .card {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                    .metric {{ display: inline-block; margin: 10px 20px; }}
                    .status {{ color: #28a745; font-weight: bold; }}
                    .error {{ color: #dc3545; }}
                    h1 {{ color: #333; }}
                    h2 {{ color: #666; }}
                </style>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
            </head>
            <body>
                <div class="container">
                    <h1>🚀 Ollama Flow Dashboard</h1>
                    
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
                        <button onclick="refreshStatus()" style="padding: 10px 20px; margin: 5px;">Refresh Status</button>
                        <button onclick="viewLogs()" style="padding: 10px 20px; margin: 5px;">View Logs</button>
                    </div>
                    
                    <div class="card">
                        <h2>Recent Tasks</h2>
                        <div id="tasks">No tasks executed yet.</div>
                    </div>
                </div>
                
                <script>
                    const socket = io();
                    
                    // Only setup SocketIO if available
                    if (typeof io !== 'undefined') {{
                        socket.on('connect', function() {{
                            console.log('Connected to dashboard');
                            refreshStatus();
                        }});
                        
                        socket.on('system_update', function(data) {{
                            updateDisplay(data);
                        }});
                    }} else {{
                        console.log('SocketIO not available, using polling');
                        refreshStatus();
                    }}
                    
                    function refreshStatus() {{
                        fetch('/api/status')
                            .then(response => response.json())
                            .then(data => updateDisplay(data))
                            .catch(error => console.error('Error:', error));
                    }}
                    
                    function updateDisplay(data) {{
                        if (data.system) {{
                            document.getElementById('status').textContent = data.system.running ? 'Running' : 'Stopped';
                            document.getElementById('timestamp').textContent = 'Last updated: ' + data.system.timestamp;
                        }}
                        if (data.resources) {{
                            document.getElementById('cpu').textContent = data.resources.cpu_percent.toFixed(1);
                            document.getElementById('memory').textContent = data.resources.memory_percent.toFixed(1);
                            document.getElementById('disk').textContent = data.resources.disk_percent.toFixed(1);
                        }}
                    }}
                    
                    function viewLogs() {{
                        alert('Logs feature coming soon!');
                    }}
                    
                    // Auto-refresh every 5 seconds
                    setInterval(refreshStatus, 5000);
                </script>
            </body>
            </html>
            """
        
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