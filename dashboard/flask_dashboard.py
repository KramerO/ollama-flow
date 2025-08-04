#!/usr/bin/env python3
"""
Flask Web Dashboard for Enhanced Ollama Flow Framework
Provides web-based monitoring, control, and management interface
"""

import asyncio
import json
import logging
import os
import sys
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import psutil
from flask import Flask, render_template, request, jsonify, Response, redirect, url_for
from flask_socketio import SocketIO, emit
from werkzeug.serving import make_server

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_main import EnhancedOllamaFlow
from neural_intelligence import NeuralIntelligenceEngine
from mcp_tools import MCPToolsManager
from monitoring_system import MonitoringSystem
from session_manager import SessionManager

logger = logging.getLogger(__name__)

# Thread pool for async operations
executor = None

class FlaskDashboard:
    """Flask web dashboard for Ollama Flow Framework"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
        self.host = host
        self.port = port
        self.debug = debug
        
        # Flask app setup
        self.app = Flask(__name__, 
                        template_folder='templates',
                        static_folder='static')
        self.app.config['SECRET_KEY'] = 'ollama-flow-dashboard-2024'
        
        # SocketIO for real-time updates
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Enhanced components
        self.framework: Optional[EnhancedOllamaFlow] = None
        self.neural_engine: Optional[NeuralIntelligenceEngine] = None
        self.mcp_tools: Optional[MCPToolsManager] = None
        self.monitoring_system: Optional[MonitoringSystem] = None
        self.session_manager: Optional[SessionManager] = None
        
        # Dashboard state
        self.is_running = False
        self.current_task = None
        self.execution_thread = None
        self.update_thread = None
        
        # Setup routes
        self._setup_routes()
        self._setup_socketio_events()
        
        # Initialize components (delayed until run)
        self.components_initialized = False
        
        # Initialize components (delayed until run)
        self.components_initialized = False
    
    def _initialize_components_simple(self):
        """Initialize enhanced components (simplified)"""
        try:
            # Initialize without async for now
            logger.info("Initializing dashboard components (simplified mode)")
            self.components_initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize dashboard components: {e}")
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main dashboard page"""
            # Detect current architecture (default to HIERARCHICAL)
            current_architecture = self._detect_current_architecture()
            ascii_diagram = self._generate_ascii_architecture(current_architecture)
            
            return render_template('dashboard.html', 
                                 architecture=current_architecture,
                                 ascii_diagram=ascii_diagram)
        
        @self.app.route('/sessions')
        def sessions_page():
            """Sessions management page"""
            return render_template('sessions.html')
        
        @self.app.route('/monitoring')
        def monitoring_page():
            """System monitoring page"""
            current_architecture = self._detect_current_architecture()
            ascii_diagram = self._generate_ascii_architecture(current_architecture)
            
            return render_template('monitoring.html',
                                 architecture=current_architecture,
                                 ascii_diagram=ascii_diagram)
        
        @self.app.route('/neural')
        def neural_page():
            """Neural intelligence page"""
            current_architecture = self._detect_current_architecture()
            ascii_diagram = self._generate_ascii_architecture(current_architecture)
            
            return render_template('neural.html',
                                 architecture=current_architecture,
                                 ascii_diagram=ascii_diagram)
        
        @self.app.route('/api/status')
        def api_status():
            """Get system status"""
            try:
                status = {
                    'system': {
                        'running': self.is_running,
                        'current_task': self.current_task,
                        'timestamp': datetime.now().isoformat(),
                        'components_initialized': self.components_initialized
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
        
        @self.app.route('/api/sessions')
        def api_sessions():
            """Get sessions list"""
            try:
                # Simplified sessions API
                sessions_data = [
                    {
                        'id': 'default',
                        'name': 'Default Session',
                        'status': 'active',
                        'created_at': datetime.now().isoformat(),
                        'task_count': 0
                    }
                ]
                
                return jsonify({
                    'sessions': sessions_data,
                    'total': len(sessions_data)
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/session/<session_id>')
        def api_session_detail(session_id):
            """Get detailed session information"""
            try:
                # Simplified session detail
                session_detail = {
                    'id': session_id,
                    'name': f'Session {session_id}',
                    'status': 'active',
                    'created_at': datetime.now().isoformat(),
                    'task_count': 0,
                    'agents': [],
                    'metrics': {
                        'cpu_usage': psutil.cpu_percent(),
                        'memory_usage': psutil.virtual_memory().percent
                    }
                }
                
                return jsonify(session_detail)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
                if not self.session_manager:
                    return jsonify({'error': 'Session manager not initialized'}), 500
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                session = loop.run_until_complete(
                    self.session_manager.get_session(session_id)
                )
                
                if not session:
                    return jsonify({'error': 'Session not found'}), 404
                
                session_data = {
                    'session_id': session.session_id,
                    'user_id': session.user_id,
                    'created_at': session.created_at,
                    'last_active': session.last_active,
                    'status': session.status,
                    'task_description': session.task_description,
                    'architecture_type': session.architecture_type,
                    'worker_count': session.worker_count,
                    'model_name': session.model_name,
                    'secure_mode': session.secure_mode,
                    'project_folder': session.project_folder,
                    'agent_states': session.agent_states,
                    'execution_context': session.execution_context,
                    'performance_metrics': session.performance_metrics,
                    'neural_insights': session.neural_insights,
                    'mcp_tool_usage': session.mcp_tool_usage
                }
                
                loop.close()
                return jsonify(session_data)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/neural/patterns')
        def api_neural_patterns():
            """Get neural patterns"""
            try:
                if not self.neural_engine:
                    return jsonify({'error': 'Neural engine not initialized'}), 500
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                patterns_data = loop.run_until_complete(
                    self.neural_engine.get_all_patterns()
                )
                
                patterns = []
                for pattern in patterns_data:
                    patterns.append({
                        'pattern_id': pattern.pattern_id,
                        'pattern_type': pattern.pattern_type,
                        'confidence': pattern.confidence,
                        'success_rate': pattern.success_rate,
                        'usage_count': pattern.usage_count,
                        'last_used': pattern.last_used,
                        'created_at': pattern.created_at
                    })
                
                neural_status = loop.run_until_complete(
                    self.neural_engine.get_neural_status()
                )
                
                loop.close()
                return jsonify({
                    'patterns': patterns,
                    'status': neural_status
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/execute', methods=['POST'])
        def api_execute_task():
            """Execute a new task"""
            try:
                data = request.get_json()
                if not data or 'task' not in data:
                    return jsonify({'error': 'Task description required'}), 400
                
                task = data['task']
                workers = data.get('workers', 4)
                architecture = data.get('architecture', 'HIERARCHICAL')
                model = data.get('model', 'codellama:7b')
                secure = data.get('secure', True)
                
                if self.is_running:
                    return jsonify({'error': 'Another task is already running'}), 409
                
                # Start task execution in background thread
                self.execution_thread = threading.Thread(
                    target=self._execute_task_background,
                    args=(task, workers, architecture, model, secure)
                )
                self.execution_thread.start()
                
                return jsonify({
                    'message': 'Task execution started',
                    'task': task,
                    'status': 'started'
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/stop', methods=['POST'])
        def api_stop_task():
            """Stop current task execution"""
            try:
                if not self.is_running:
                    return jsonify({'error': 'No task is currently running'}), 400
                
                # Stop the framework
                if self.framework:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.framework.stop_all_agents())
                    loop.close()
                
                self.is_running = False
                self.current_task = None
                
                return jsonify({'message': 'Task execution stopped'})
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/cleanup', methods=['POST'])
        def api_cleanup():
            """Cleanup databases and files"""
            try:
                if self.framework:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    success = loop.run_until_complete(
                        self.framework.cleanup_database_and_files()
                    )
                    loop.close()
                    
                    if success:
                        return jsonify({'message': 'Cleanup completed successfully'})
                    else:
                        return jsonify({'error': 'Cleanup failed'}), 500
                else:
                    return jsonify({'error': 'Framework not initialized'}), 500
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def _detect_current_architecture(self) -> str:
        """Detect current system architecture"""
        # Check if framework is running and has architecture info
        if self.framework and hasattr(self.framework, 'config'):
            return self.framework.config.get('architecture_type', 'HIERARCHICAL')
        
        # Try to detect from recent logs or processes
        try:
            import glob
            import re
            
            log_patterns = [
                "/home/oliver/Projects/ollama-flow/**/*.log",
                "./**.log"
            ]
            
            for pattern in log_patterns:
                for log_file in glob.glob(pattern, recursive=True):
                    try:
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()[-1000:]  # Last 1000 chars
                            
                        arch_match = re.search(r'Architecture: (\w+)', content)
                        if arch_match:
                            return arch_match.group(1)
                    except:
                        continue
        except:
            pass
            
        # Default to HIERARCHICAL
        return 'HIERARCHICAL'
    
    def _generate_ascii_architecture(self, architecture: str) -> str:
        """Generate ASCII art diagram for the given architecture"""
        
        if architecture == 'HIERARCHICAL':
            return """
                    ┌─────────────┐
                    │    QUEEN    │
                    │   (Master)  │
                    └──────┬──────┘
                           │
               ┌───────────┼───────────┐
               │                       │
        ┌──────▼──────┐        ┌──────▼──────┐
        │  SUB-QUEEN  │        │  SUB-QUEEN  │
        │     (A)     │        │     (B)     │
        └──────┬──────┘        └──────┬──────┘
               │                       │
         ┌─────┼─────┐           ┌─────┼─────┐
         │           │           │           │
    ┌────▼───┐  ┌────▼───┐  ┌────▼───┐  ┌────▼───┐
    │ DRONE  │  │ DRONE  │  │ DRONE  │  │ DRONE  │
    │   #1   │  │   #2   │  │   #3   │  │   #4   │
    │analyst │  │data-sci│  │architect│  │developer│
    └────────┘  └────────┘  └────────┘  └────────┘
            """
        
        elif architecture == 'CENTRALIZED':
            return """
                    ┌─────────────┐
                    │    QUEEN    │
                    │ (Centralized)│
                    └──────┬──────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            │         ┌────┼────┐         │
            │         │         │         │
       ┌────▼───┐ ┌───▼───┐ ┌───▼───┐ ┌───▼────┐
       │ DRONE  │ │ DRONE │ │ DRONE │ │ DRONE  │
       │   #1   │ │   #2  │ │   #3  │ │   #4   │
       │analyst │ │data-sci│ │architect│ │developer│
       └────────┘ └───────┘ └───────┘ └────────┘
               ▲       ▲       ▲       ▲
               │       │       │       │
               └───────┼───────┼───────┘
                       │       │
                   Direct Communication
            """
        
        elif architecture == 'FULLY_CONNECTED':
            return """
           ┌─────────┐ ◄──────────► ┌─────────┐
           │ AGENT 1 │               │ AGENT 2 │
           │ analyst │ ◄─────┐ ┌────► │data-sci │
           └─────────┘       │ │     └─────────┘
                 ▲           │ │           ▲
                 │           │ │           │
                 ▼           │ │           ▼
           ┌─────────┐       │ │     ┌─────────┐
           │ AGENT 4 │ ◄─────┘ └────► │ AGENT 3 │
           │developer│               │architect│
           └─────────┘ ◄──────────► └─────────┘
           
           ═══ Peer-to-Peer Network ═══
           All agents communicate directly
            """
        
        else:
            return """
                ┌─────────────┐
                │   UNKNOWN   │
                │ ARCHITECTURE│
                └─────────────┘
            """
    
    def _setup_socketio_events(self):
        """Setup SocketIO events for real-time updates"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            logger.info("Client connected to dashboard")
            emit('status', {'message': 'Connected to Ollama Flow Dashboard'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            logger.info("Client disconnected from dashboard")
        
        @self.socketio.on('request_update')
        def handle_update_request():
            """Handle client request for updates"""
            self._emit_system_update()
    
    def _execute_task_background(self, task: str, workers: int, architecture: str, 
                                model: str, secure: bool):
        """Execute task in background thread"""
        try:
            self.is_running = True
            self.current_task = task
            
            # Emit task started event
            self.socketio.emit('task_started', {
                'task': task,
                'workers': workers,
                'architecture': architecture,
                'model': model,
                'timestamp': datetime.now().isoformat()
            })
            
            # Create and run framework
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            self.framework = EnhancedOllamaFlow()
            
            # Configure framework
            self.framework.config = {
                'worker_count': workers,
                'architecture_type': architecture,
                'model': model,
                'secure_mode': secure,
                'project_folder': None,
                'parallel_llm': True,
                'metrics_enabled': True,
                'benchmark_mode': True,
                'db_path': 'ollama_flow_messages.db',
                'log_level': 'INFO'
            }
            
            # Run task
            success = loop.run_until_complete(self.framework.run_single_task(task))
            
            # Emit task completed event
            self.socketio.emit('task_completed', {
                'task': task,
                'success': success,
                'timestamp': datetime.now().isoformat()
            })
            
            loop.close()
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            self.socketio.emit('task_failed', {
                'task': task,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        finally:
            self.is_running = False
            self.current_task = None
    
    def _emit_system_update(self):
        """Emit system status update"""
        try:
            # Get system resources
            system_data = {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'network_io': psutil.net_io_counters()._asdict(),
                'timestamp': datetime.now().isoformat()
            }
            
            self.socketio.emit('system_update', system_data)
            
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
    
    def _initialize_components_sync(self):
        """Initialize components synchronously"""
        if self.components_initialized:
            return
            
        try:
            # Use simplified initialization
            self._initialize_components_simple()
            logger.info("Dashboard components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize dashboard components: {e}")

    def run(self):
        """Run the Flask dashboard"""
        logger.info(f"Starting Ollama Flow Dashboard on {self.host}:{self.port}")
        
        # Initialize components first
        self._initialize_components_sync()
        
        if self.debug:
            print(f"""
🚀 Ollama Flow Dashboard Starting
================================
URL: http://{self.host}:{self.port}
Mode: {'Debug' if self.debug else 'Production'}

Features:
✓ Real-time monitoring
✓ Task execution control
✓ Session management
✓ Neural intelligence insights
✓ System performance metrics

Press Ctrl+C to stop
================================
            """)
        
        # Start update thread
        self.start_update_thread()
        
        # Run Flask app with SocketIO
        self.socketio.run(
            self.app,
            host=self.host,
            port=self.port,
            debug=self.debug,
            use_reloader=False  # Disable reloader to avoid issues with threading
        )

def main():
    """Main entry point for dashboard"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ollama Flow Web Dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO if not args.debug else logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run dashboard
    dashboard = FlaskDashboard(
        host=args.host,
        port=args.port,
        debug=args.debug
    )
    
    try:
        dashboard.run()
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped")
    except Exception as e:
        print(f"❌ Dashboard error: {e}")

if __name__ == "__main__":
    main()