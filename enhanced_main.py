#!/usr/bin/env python3
"""
Enhanced Ollama Flow Framework - Main Entry Point
Supports parallel task processing with intelligent agent coordination
"""

import asyncio
import os
import argparse
import logging
import json
import signal
import psutil
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

from orchestrator.orchestrator import Orchestrator
from agents.enhanced_queen_agent import EnhancedQueenAgent
from agents.enhanced_sub_queen_agent import EnhancedSubQueenAgent
from agents.secure_worker_agent import SecureWorkerAgent
from db_manager import MessageDBManager
from neural_intelligence import NeuralIntelligenceEngine
from mcp_tools import MCPToolsManager
from monitoring_system import MonitoringSystem
from session_manager import SessionManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ollama_flow.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class EnhancedOllamaFlow:
    """Enhanced Ollama Flow Framework with parallel processing capabilities"""
    
    def __init__(self):
        self.db_manager: Optional[MessageDBManager] = None
        self.orchestrator: Optional[Orchestrator] = None
        self.config: Dict[str, Any] = {}
        self.agents_info: Dict[str, Any] = {}
        self.running_processes: List[asyncio.Task] = []
        
        # Enhanced components
        self.neural_engine: Optional[NeuralIntelligenceEngine] = None
        self.mcp_tools: Optional[MCPToolsManager] = None
        self.monitoring_system: Optional[MonitoringSystem] = None
        self.session_manager: Optional[SessionManager] = None
        
    def parse_arguments(self) -> argparse.Namespace:
        """Parse command line arguments with enhanced options"""
        parser = argparse.ArgumentParser(
            description="Enhanced Ollama Flow Framework with Parallel Processing",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s --task "Build a web scraper" --workers 4 --arch HIERARCHICAL
  %(prog)s --task "Analyze data file" --workers 2 --arch CENTRALIZED --secure
  %(prog)s --interactive --project-folder ./my_project
            """
        )
        
        # Task specification
        parser.add_argument(
            "--task", 
            type=str, 
            help="The main task prompt for the orchestrator"
        )
        
        parser.add_argument(
            "--interactive", "-i",
            action="store_true",
            help="Run in interactive mode"
        )
        
        parser.add_argument(
            "--web-dashboard",
            action="store_true", 
            help="Launch web dashboard interface"
        )
        
        # Agent configuration
        parser.add_argument(
            "--workers", "--worker-count",
            type=int,
            help="Number of worker agents (default: from env or 4)"
        )
        
        parser.add_argument(
            "--sub-queens",
            type=int,
            help="Number of sub-queen agents for hierarchical mode (default: 2)"
        )
        
        parser.add_argument(
            "--arch", "--architecture",
            choices=["HIERARCHICAL", "CENTRALIZED", "FULLY_CONNECTED"],
            help="Architecture type (default: HIERARCHICAL)"
        )
        
        # Model and performance
        parser.add_argument(
            "--model",
            type=str,
            help="Ollama model to use (default: phi3:mini)"
        )
        
        parser.add_argument(
            "--parallel-llm",
            action="store_true",
            help="Enable parallel LLM calls for better performance"
        )
        
        # Security and sandboxing
        parser.add_argument(
            "--secure",
            action="store_true",
            help="Enable enhanced security mode with command sandboxing"
        )
        
        parser.add_argument(
            "--project-folder",
            type=str,
            help="Project folder path for agent file operations (default: current directory)"
        )
        
        # Database and logging
        parser.add_argument(
            "--db-path",
            type=str,
            default="ollama_flow_messages.db",
            help="Database path for message storage"
        )
        
        parser.add_argument(
            "--log-level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR"],
            default="INFO",
            help="Logging level"
        )
        
        # Performance monitoring
        parser.add_argument(
            "--metrics",
            action="store_true",
            help="Enable performance metrics collection"
        )
        
        parser.add_argument(
            "--benchmark",
            action="store_true",
            help="Run in benchmark mode with performance timing"
        )
        
        # Control commands
        parser.add_argument(
            "--stop-agents",
            action="store_true",
            help="Stop all running agents and cleanup processes"
        )
        
        parser.add_argument(
            "--cleanup",
            action="store_true",
            help="Clean up database and temporary files"
        )
        
        return parser.parse_args()

    def load_configuration(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Load configuration from environment and arguments"""
        config = {
            # Worker configuration
            'worker_count': args.workers or int(os.getenv("OLLAMA_WORKER_COUNT", "4")),
            'sub_queen_count': args.sub_queens or int(os.getenv("OLLAMA_SUB_QUEEN_COUNT", "2")),
            'architecture_type': args.arch or os.getenv("OLLAMA_ARCHITECTURE_TYPE", "HIERARCHICAL"),
            
            # Model configuration
            'model': args.model or os.getenv("OLLAMA_MODEL", "phi3:mini"),
            'parallel_llm': args.parallel_llm or os.getenv("OLLAMA_PARALLEL_LLM", "").lower() == "true",
            
            # Security configuration
            'secure_mode': args.secure or os.getenv("OLLAMA_SECURE_MODE", "").lower() == "true",
            'project_folder': self._resolve_project_folder(args.project_folder or os.getenv("OLLAMA_PROJECT_FOLDER")),
            
            # Database and logging
            'db_path': args.db_path,
            'log_level': args.log_level,
            
            # Performance
            'metrics_enabled': args.metrics or os.getenv("OLLAMA_METRICS", "").lower() == "true",
            'benchmark_mode': args.benchmark,
            
            # Interactive mode
            'interactive': args.interactive,
            'task': args.task,
            'web_dashboard': args.web_dashboard,
            
            # Control commands
            'stop_agents': args.stop_agents,
            'cleanup': args.cleanup
        }
        
        # Validate configuration
        if config['worker_count'] <= 0:
            config['worker_count'] = 4
            
        if config['sub_queen_count'] <= 0:
            config['sub_queen_count'] = 2
            
        return config
    
    def _resolve_project_folder(self, project_folder: str = None) -> str:
        """Resolve and validate project folder"""
        # Use current working directory if no project folder specified
        if not project_folder:
            project_folder = os.getcwd()
            print(f"🔍 No project folder specified, using current directory: {project_folder}")
        
        # Make sure we have absolute path
        project_folder = os.path.abspath(project_folder)
        
        # Ensure project folder exists
        if not os.path.exists(project_folder):
            print(f"📁 Creating project folder: {project_folder}")
            os.makedirs(project_folder, exist_ok=True)
        
        # Verify it's a directory
        if not os.path.isdir(project_folder):
            raise ValueError(f"Project folder path is not a directory: {project_folder}")
        
        print(f"✅ Using project folder: {project_folder}")
        return project_folder

    async def setup_database(self) -> MessageDBManager:
        """Initialize database manager"""
        try:
            db_manager = MessageDBManager(db_path=self.config['db_path'])
            logger.info(f"Database initialized: {self.config['db_path']}")
            return db_manager
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    async def setup_orchestrator(self, db_manager: MessageDBManager) -> Orchestrator:
        """Initialize orchestrator"""
        try:
            orchestrator = Orchestrator(db_manager, model=self.config['model'])
            return orchestrator
        except Exception as e:
            logger.error(f"Orchestrator initialization failed: {e}")
            raise

    async def create_enhanced_agents(self, orchestrator: Orchestrator) -> Dict[str, Any]:
        """Create and register enhanced agents"""
        agents_info = {
            'queen': None,
            'sub_queens': [],
            'workers': [],
            'total_agents': 0
        }
        
        try:
            # Create Enhanced Queen Agent
            queen_agent = EnhancedQueenAgent(
                agent_id="enhanced-queen-1",
                name="Enhanced Main Queen",
                architecture_type=self.config['architecture_type'],
                model=self.config['model']
            )
            # Don't initialize queen yet - wait until all agents are registered
            agents_info['queen'] = queen_agent
            agents_info['total_agents'] += 1
            
            # Create Worker Agents (Secure or Standard)
            worker_agents = []
            WorkerClass = SecureWorkerAgent if self.config['secure_mode'] else SecureWorkerAgent  # Always use secure
            
            for i in range(self.config['worker_count']):
                worker = WorkerClass(
                    agent_id=f"secure-worker-{i+1}",
                    name=f"Secure Worker {i+1}",
                    model=self.config['model'],
                    project_folder_path=self.config['project_folder']
                )
                worker_agents.append(worker)
                orchestrator.register_agent(worker)
                agents_info['total_agents'] += 1
                
            agents_info['workers'] = worker_agents
            
            # Create Sub-Queen Agents for Hierarchical Architecture
            if self.config['architecture_type'] == 'HIERARCHICAL':
                sub_queen_agents = []
                sub_queen_groups = [[] for _ in range(self.config['sub_queen_count'])]
                
                # Distribute workers among sub-queens
                for i, worker in enumerate(worker_agents):
                    group_index = i % self.config['sub_queen_count']
                    sub_queen_groups[group_index].append(worker)
                
                # Create sub-queen agents
                for i in range(self.config['sub_queen_count']):
                    sub_queen = EnhancedSubQueenAgent(
                        agent_id=f"enhanced-sub-queen-{i+1}",
                        name=f"Enhanced Sub Queen {chr(65+i)}",  # A, B, C, etc.
                        model=self.config['model']
                    )
                    sub_queen.initialize_group_agents(sub_queen_groups[i])
                    orchestrator.register_agent(sub_queen)
                    sub_queen_agents.append(sub_queen)
                    agents_info['total_agents'] += 1
                    
                agents_info['sub_queens'] = sub_queen_agents
                
            # Register and initialize Queen Agent AFTER all other agents are registered
            orchestrator.register_agent(queen_agent)
            queen_agent.initialize_agents()
            
            logger.info(f"Created {agents_info['total_agents']} enhanced agents:")
            logger.info(f"  - Queen: 1")
            logger.info(f"  - Sub-Queens: {len(agents_info['sub_queens'])}")
            logger.info(f"  - Workers: {len(agents_info['workers'])}")
            
            return agents_info
            
        except Exception as e:
            logger.error(f"Agent creation failed: {e}")
            raise

    async def get_task_input(self) -> str:
        """Get task input from user or arguments"""
        if self.config['task']:
            return self.config['task']
            
        if self.config['interactive']:
            print("\n" + "="*60)
            print("🚀 Enhanced Ollama Flow Framework")
            print("="*60)
            print(f"Architecture: {self.config['architecture_type']}")
            print(f"Workers: {self.config['worker_count']}")
            print(f"Model: {self.config['model']}")
            print(f"Secure Mode: {'✓' if self.config['secure_mode'] else '✗'}")
            if self.config['project_folder']:
                print(f"Project Folder: {self.config['project_folder']}")
            print("="*60)
            print("📋 Available commands:")
            print("  • 'stop' or 'stop agents' - Stop all running agents")
            print("  • 'cleanup' or 'clean' - Clean database and temp files")
            print("  • 'status' or 'info' - Show system status")
            print("  • 'quit' or 'exit' - Exit the framework")
            print("="*60)
            
            while True:
                task = input("\n📝 Enter your task (or 'quit' to exit): ").strip()
                if task.lower() in ['quit', 'exit', 'q']:
                    return ""
                elif task:
                    return task
                else:
                    print("Please enter a valid task.")
        else:
            # Non-interactive mode requires task argument
            print("Error: No task provided. Use --task or --interactive mode.")
            return ""

    async def execute_task(self, task: str, orchestrator: Orchestrator) -> Dict[str, Any]:
        """Execute task with performance monitoring"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            logger.info(f"Executing task: {task[:100]}...")
            
            # Start orchestrator polling
            orchestrator.start_polling()
            
            # Execute task
            result = await orchestrator.run(task)
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            return {
                'success': True,
                'result': result,
                'execution_time': execution_time,
                'error': None
            }
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"Task execution failed: {e}")
            
            return {
                'success': False,
                'result': None,
                'execution_time': execution_time,
                'error': str(e)
            }

    def display_results(self, task: str, execution_result: Dict[str, Any], agents_info: Dict[str, Any]):
        """Display execution results with metrics"""
        print("\n" + "="*80)
        print("📊 EXECUTION RESULTS")
        print("="*80)
        
        print(f"Task: {task}")
        print(f"Success: {'✓' if execution_result['success'] else '✗'}")
        print(f"Execution Time: {execution_result['execution_time']:.2f}s")
        
        if execution_result['success']:
            print(f"\n📋 Result:")
            print("-" * 40)
            print(execution_result['result'])
        else:
            print(f"\n❌ Error: {execution_result['error']}")
            
        # Display metrics if enabled
        if self.config['metrics_enabled'] or self.config['benchmark_mode']:
            print("\n📈 PERFORMANCE METRICS")
            print("-" * 40)
            
            # Agent metrics
            total_agents = agents_info['total_agents']
            print(f"Total Agents: {total_agents}")
            print(f"Parallel Efficiency: {execution_result['execution_time'] / total_agents:.2f}s per agent")
            
            # Security metrics (if secure workers)
            if self.config['secure_mode'] and agents_info['workers']:
                print("\n🔒 SECURITY METRICS")
                print("-" * 40)
                
                total_executed = 0
                total_blocked = 0
                
                for worker in agents_info['workers']:
                    if hasattr(worker, 'get_security_summary'):
                        summary = worker.get_security_summary()
                        total_executed += summary['commands_executed']
                        total_blocked += summary['commands_blocked']
                        
                print(f"Commands Executed: {total_executed}")
                print(f"Commands Blocked: {total_blocked}")
                print(f"Security Rate: {((total_executed + total_blocked - total_blocked) / max(total_executed + total_blocked, 1) * 100):.1f}%")

    async def stop_all_agents(self):
        """Stop all running agents and cleanup processes"""
        logger.info("🛑 Stopping all agents...")
        
        try:
            # Cancel all running tasks
            if self.running_processes:
                logger.info(f"Cancelling {len(self.running_processes)} running processes...")
                for task in self.running_processes:
                    if not task.done():
                        task.cancel()
                
                # Wait for tasks to complete cancellation
                await asyncio.gather(*self.running_processes, return_exceptions=True)
                self.running_processes.clear()
                logger.info("✓ All async processes stopped")
            
            # Stop orchestrator polling
            if self.orchestrator and hasattr(self.orchestrator, 'polling_task'):
                if self.orchestrator.polling_task and not self.orchestrator.polling_task.done():
                    self.orchestrator.polling_task.cancel()
                    try:
                        await self.orchestrator.polling_task
                    except asyncio.CancelledError:
                        pass
                    logger.info("✓ Orchestrator polling stopped")
            
            # Stop all agents' polling tasks
            if self.agents_info:
                stopped_agents = 0
                for agent_type, agents in self.agents_info.items():
                    if agent_type == 'total_agents':
                        continue
                        
                    if isinstance(agents, list):
                        for agent in agents:
                            if hasattr(agent, 'polling_task') and agent.polling_task:
                                if not agent.polling_task.done():
                                    agent.polling_task.cancel()
                                    try:
                                        await agent.polling_task
                                    except asyncio.CancelledError:
                                        pass
                                    stopped_agents += 1
                    elif agents and hasattr(agents, 'polling_task') and agents.polling_task:
                        if not agents.polling_task.done():
                            agents.polling_task.cancel()
                            try:
                                await agents.polling_task
                            except asyncio.CancelledError:
                                pass
                            stopped_agents += 1
                            
                logger.info(f"✓ {stopped_agents} agent polling tasks stopped")
            
            # Kill any lingering Ollama processes if needed
            await self._cleanup_ollama_processes()
            
            logger.info("🎯 All agents stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping agents: {e}")
            return False

    async def _cleanup_ollama_processes(self):
        """Clean up any lingering Ollama processes"""
        try:
            # Find processes with 'ollama' in the command line
            ollama_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'ollama' in cmdline.lower() and 'run' in cmdline.lower():
                        # Only target ollama run processes, not the main ollama daemon
                        if any(model in cmdline.lower() for model in ['llama', 'codellama', 'mistral']):
                            ollama_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if ollama_processes:
                logger.info(f"Found {len(ollama_processes)} Ollama model processes to cleanup")
                for proc in ollama_processes:
                    try:
                        proc.terminate()
                        logger.info(f"✓ Terminated Ollama process {proc.pid}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                        
                # Wait a bit for graceful termination
                await asyncio.sleep(1)
                
                # Force kill if still running
                for proc in ollama_processes:
                    try:
                        if proc.is_running():
                            proc.kill()
                            logger.info(f"✓ Force killed Ollama process {proc.pid}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            else:
                logger.info("No Ollama model processes found to cleanup")
                
        except Exception as e:
            logger.warning(f"Could not cleanup Ollama processes: {e}")

    async def cleanup_database_and_files(self):
        """Clean up database and temporary files"""
        logger.info("🧹 Cleaning up database and files...")
        
        try:
            # Close database connection first
            if self.db_manager:
                self.db_manager.close()
                logger.info("✓ Database connection closed")
            
            # Remove database file if it exists
            db_path = self.config.get('db_path', 'ollama_flow_messages.db')
            if os.path.exists(db_path):
                os.remove(db_path)
                logger.info(f"✓ Removed database file: {db_path}")
            
            # Clean up log files (keep last 3)
            log_files = [f for f in os.listdir('.') if f.startswith('ollama_flow') and f.endswith('.log')]
            if len(log_files) > 3:
                log_files.sort(key=lambda x: os.path.getmtime(x))
                for old_log in log_files[:-3]:
                    os.remove(old_log)
                    logger.info(f"✓ Removed old log file: {old_log}")
            
            # Clean up any temporary files
            temp_files = [f for f in os.listdir('.') if f.startswith('tmp_') or f.endswith('.tmp')]
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                    logger.info(f"✓ Removed temporary file: {temp_file}")
                except Exception:
                    pass
            
            logger.info("🎯 Cleanup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return False

    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.db_manager:
                self.db_manager.close()
                logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    async def run_single_task(self, task: str) -> bool:
        """Run a single task execution"""
        try:
            # Setup database
            self.db_manager = await self.setup_database()
            
            # Setup orchestrator
            self.orchestrator = await self.setup_orchestrator(self.db_manager)
            
            # Create agents
            agents_info = await self.create_enhanced_agents(self.orchestrator)
            self.agents_info = agents_info
            
            # Execute task
            execution_result = await self.execute_task(task, self.orchestrator)
            
            # Display results
            self.display_results(task, execution_result, agents_info)
            
            # Auto-shutdown: Stop all agents and cleanup after task completion
            print("\n🔄 Task completed - Shutting down agents...")
            logger.info("Task completed - Beginning automatic shutdown")
            
            # Stop all agents
            shutdown_success = await self.stop_all_agents()
            if shutdown_success:
                print("✅ All agents stopped successfully")
                logger.info("✅ All agents stopped successfully")
            else:
                print("⚠️ Some agents may still be running")
                logger.warning("⚠️ Some agents may still be running")
            
            # Cleanup resources
            await self.cleanup()
            print("✅ System cleanup completed")
            logger.info("✅ System cleanup completed")
            
            # Final success message
            print("\n" + "="*60)
            if execution_result['success']:
                print("🎉 TASK SUCCESSFULLY COMPLETED")
                print("✅ All agents have been stopped")
                print("✅ System resources cleaned up") 
                print("✅ Ollama Flow terminated gracefully")
                logger.info("🎉 Task completed successfully - All agents stopped - System terminated")
            else:
                print("⚠️ TASK COMPLETED WITH ISSUES")
                print("✅ All agents have been stopped")
                print("✅ System resources cleaned up")
                print("✅ Ollama Flow terminated gracefully")
                logger.info("⚠️ Task completed with errors - All agents stopped - System terminated")
            print("="*60)
            
            return execution_result['success']
            
        except Exception as e:
            logger.error(f"Single task execution failed: {e}")
            print(f"\n❌ Framework Error: {e}")
            return False

    async def run_interactive_mode(self):
        """Run in interactive mode"""
        try:
            # Setup database and orchestrator once
            self.db_manager = await self.setup_database()
            self.orchestrator = await self.setup_orchestrator(self.db_manager)
            agents_info = await self.create_enhanced_agents(self.orchestrator)
            self.agents_info = agents_info
            
            while True:
                task = await self.get_task_input()
                if not task:
                    break
                
                # Check for interactive commands
                if task.lower().strip() in ['stop', 'stop agents']:
                    print("\n🛑 Stopping all agents...")
                    success = await self.stop_all_agents()
                    if success:
                        print("✅ All agents stopped successfully")
                    else:
                        print("❌ Failed to stop some agents")
                    continue
                    
                elif task.lower().strip() in ['cleanup', 'clean']:
                    print("\n🧹 Cleaning up database and files...")
                    success = await self.cleanup_database_and_files()
                    if success:
                        print("✅ Cleanup completed successfully")
                        # Reinitialize after cleanup
                        self.db_manager = await self.setup_database()
                        self.orchestrator = await self.setup_orchestrator(self.db_manager)
                        agents_info = await self.create_enhanced_agents(self.orchestrator)
                        self.agents_info = agents_info
                    else:
                        print("❌ Cleanup failed")
                    continue
                
                elif task.lower().strip() in ['status', 'info']:
                    print(f"\n📊 SYSTEM STATUS")
                    print("="*40)
                    print(f"Total Agents: {agents_info['total_agents']}")
                    print(f"Queen: {'✓' if agents_info['queen'] else '✗'}")
                    print(f"Sub-Queens: {len(agents_info['sub_queens'])}")
                    print(f"Workers: {len(agents_info['workers'])}")
                    print(f"Architecture: {self.config['architecture_type']}")
                    print(f"Model: {self.config['model']}")
                    print(f"Secure Mode: {'✓' if self.config['secure_mode'] else '✗'}")
                    continue
                    
                print(f"\n🚀 Processing task: {task}")
                
                execution_result = await self.execute_task(task, self.orchestrator)
                self.display_results(task, execution_result, agents_info)
                
                print("\n" + "-"*60)
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
        except Exception as e:
            logger.error(f"Interactive mode failed: {e}")
            print(f"\n❌ Framework Error: {e}")

    async def run_web_dashboard(self):
        """Run web dashboard interface"""
        try:
            print("\n" + "="*60)
            print("🌐 OLLAMA FLOW WEB DASHBOARD")
            print("="*60)
            print("🚀 Starting web dashboard server...")
            
            # Check if dashboard file exists
            dashboard_path = os.path.join(os.path.dirname(__file__), 'dashboard', 'flask_dashboard.py')
            if not os.path.exists(dashboard_path):
                print("❌ Web dashboard not found!")
                print(f"Expected at: {dashboard_path}")
                print("\n💡 The web dashboard feature is not yet implemented.")
                print("Available alternatives:")
                print("  • ollama-flow --interactive    - Interactive CLI mode")
                print("  • ollama-flow run 'task'       - Direct task execution")
                print("  • ollama-flow status           - System status")
                return
            
            # Import and run dashboard
            import sys
            sys.path.insert(0, os.path.dirname(dashboard_path))
            
            try:
                import flask_dashboard
                
                # Create dashboard instance
                dashboard = flask_dashboard.FlaskDashboard(host='0.0.0.0', port=5001, debug=False)
                app = dashboard.app
                
                print("✅ Dashboard loaded successfully")
                print("🌐 Web dashboard will be available at: http://localhost:5001")
                print("\n💡 Press Ctrl+C to stop the dashboard")
                print("="*60)
                
                # Setup routes and run dashboard
                dashboard.setup_routes()
                dashboard.run()
                
            except AttributeError:
                # Fallback: try to get app directly
                try:
                    import flask_dashboard
                    app = flask_dashboard.app if hasattr(flask_dashboard, 'app') else None
                    if app:
                        app.run(host='0.0.0.0', port=5000, debug=False)
                    else:
                        raise ImportError("No app found in flask_dashboard")
                except Exception:
                    # Create simple fallback dashboard
                    from flask import Flask
                    app = Flask(__name__)
                    
                    @app.route('/')
                    def dashboard():
                        return '''
                        <!DOCTYPE html>
                        <html>
                        <head><title>Ollama Flow Dashboard</title></head>
                        <body>
                        <h1>🚀 Ollama Flow Dashboard</h1>
                        <p>✅ Dashboard is running!</p>
                        <p>💡 This is a basic fallback dashboard.</p>
                        <a href="/status">System Status</a>
                        </body>
                        </html>
                        '''
                    
                    @app.route('/status')
                    def status():
                        return '''
                        <!DOCTYPE html>
                        <html>
                        <head><title>System Status</title></head>
                        <body>
                        <h2>📊 System Status</h2>
                        <p>✅ Ollama Flow Framework: Running</p>
                        <p>🔧 Mode: Web Dashboard</p>
                        <p>⚡ Model: phi3:mini (default)</p>
                        <a href="/">Back to Dashboard</a>
                        </body>
                        </html>
                        '''
                    
                    print("✅ Simple dashboard loaded")
                    print("🌐 Web dashboard available at: http://localhost:5000")
                    print("\n💡 Press Ctrl+C to stop")
                    print("="*60)
                    
                    app.run(host='0.0.0.0', port=5000, debug=False)
                
            except ImportError as e:
                print(f"❌ Could not import dashboard: {e}")
                print("\n💡 Installing Flask might be needed:")
                print("  pip install flask flask-socketio")
                
        except Exception as e:
            logger.error(f"Web dashboard failed: {e}")
            print(f"\n❌ Dashboard Error: {e}")
            print("\n💡 Try using interactive mode instead:")
            print("  ollama-flow --interactive")

    async def main(self):
        """Main execution flow"""
        try:
            # Parse arguments and load configuration
            args = self.parse_arguments()
            self.config = self.load_configuration(args)
            
            # Set log level
            logging.getLogger().setLevel(getattr(logging, self.config['log_level']))
            
            # Handle control commands first
            if self.config['stop_agents']:
                logger.info("🛑 Stop agents command received...")
                success = await self.stop_all_agents()
                if success:
                    print("✅ All agents stopped successfully")
                    exit(0)
                else:
                    print("❌ Failed to stop some agents")
                    exit(1)
            
            if self.config['cleanup']:
                logger.info("🧹 Cleanup command received...")
                success = await self.cleanup_database_and_files()
                if success:
                    print("✅ Cleanup completed successfully")
                    exit(0)
                else:
                    print("❌ Cleanup failed")
                    exit(1)
            
            logger.info("Enhanced Ollama Flow Framework starting...")
            logger.info(f"Configuration: {json.dumps(self.config, indent=2)}")
            
            if self.config['web_dashboard']:
                await self.run_web_dashboard()
            elif self.config['interactive']:
                await self.run_interactive_mode()
            else:
                task = await self.get_task_input()
                if task:
                    success = await self.run_single_task(task)
                    exit(0 if success else 1)
                else:
                    exit(1)
                    
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            print("\n👋 Goodbye!")
        except Exception as e:
            logger.error(f"Framework error: {e}")
            print(f"\n❌ Critical Error: {e}")
            exit(1)
        finally:
            await self.cleanup()

def main():
    """Entry point"""
    try:
        framework = EnhancedOllamaFlow()
        asyncio.run(framework.main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Startup Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()