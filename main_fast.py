import asyncio
import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

from orchestrator.orchestrator import Orchestrator
from agents.queen_agent import QueenAgent
from agents.sub_queen_agent import SubQueenAgent
from agents.worker_agent import WorkerAgent
from db_manager import MessageDBManager
from config import OllamaFlowConfig, get_config, init_logging
from llm_backend import EnhancedLLMBackendManager
from exceptions import ConfigurationException, BackendUnavailableException

load_dotenv()

def setup_gpu_optimizations(args):
    """Setup GPU optimization environment variables based on CLI arguments"""
    
    # Performance mode mapping
    performance_modes = {
        "eco": {
            "OLLAMA_GPU_LAYERS": "20",
            "OLLAMA_NUM_PARALLEL": "4", 
            "OLLAMA_MAX_LOADED_MODELS": "2",
            "OMP_NUM_THREADS": "4"
        },
        "balanced": {
            "OLLAMA_GPU_LAYERS": "35",
            "OLLAMA_NUM_PARALLEL": "8",
            "OLLAMA_MAX_LOADED_MODELS": "4", 
            "OMP_NUM_THREADS": "8"
        },
        "performance": {
            "OLLAMA_GPU_LAYERS": "45",
            "OLLAMA_NUM_PARALLEL": "12",
            "OLLAMA_MAX_LOADED_MODELS": "6",
            "OMP_NUM_THREADS": "12"
        },
        "max": {
            "OLLAMA_GPU_LAYERS": "50",
            "OLLAMA_NUM_PARALLEL": "16", 
            "OLLAMA_MAX_LOADED_MODELS": "8",
            "OMP_NUM_THREADS": "16"
        }
    }
    
    # Apply performance mode settings
    if args.performance_mode in performance_modes:
        mode_settings = performance_modes[args.performance_mode]
        for key, value in mode_settings.items():
            os.environ[key] = value
        print(f"🎯 Applied GPU performance mode: {args.performance_mode}")
    
    # Override with specific CLI arguments if provided
    if args.gpu_layers:
        os.environ["OLLAMA_GPU_LAYERS"] = str(args.gpu_layers)
        print(f"🔧 GPU layers set to: {args.gpu_layers}")
    
    if args.parallel_requests:
        os.environ["OLLAMA_NUM_PARALLEL"] = str(args.parallel_requests)
        print(f"🔧 Parallel requests set to: {args.parallel_requests}")
    
    # Enable GPU acceleration
    if args.gpu_enabled:
        os.environ["OLLAMA_GPU_ACCELERATION"] = "true"
        print("🚀 GPU acceleration enabled")
    
    # GPU monitoring
    if args.gpu_monitoring:
        os.environ["OLLAMA_GPU_MONITORING"] = "true"
        print("📊 GPU monitoring enabled")
    
    # Auto-scaling
    if args.auto_scale:
        os.environ["OLLAMA_AUTO_SCALE"] = "true"
        print("⚡ Auto-scaling enabled")

async def launch_dashboard():
    """Launch web dashboard"""
    try:
        import subprocess
        import sys
        
        # Try to launch dashboard from different locations
        dashboard_paths = [
            "/home/oliver/.ollama-flow/dashboard/simple_dashboard.py",
            "/home/oliver/projects/ollama-flow/dashboard/simple_dashboard.py",
            "dashboard/simple_dashboard.py"
        ]
        
        dashboard_script = None
        for path in dashboard_paths:
            if Path(path).exists():
                dashboard_script = path
                break
        
        if dashboard_script:
            print("🌐 Launching web dashboard...")
            subprocess.run([sys.executable, dashboard_script], check=True)
        else:
            print("❌ Dashboard not found. Available paths:")
            for path in dashboard_paths:
                print(f"   - {path}")
            print("\n💡 Try: python3 dashboard/simple_dashboard.py")
            
    except Exception as e:
        print(f"❌ Failed to launch dashboard: {e}")

def stop_all_agents():
    """Stop all running agents"""
    try:
        import subprocess
        import signal
        import psutil
        
        print("🛑 Stopping all ollama-flow agents...")
        
        # Kill processes by name
        killed_count = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if ('ollama-flow' in cmdline or 
                    'main_fast.py' in cmdline or 
                    'main.py' in cmdline or 
                    'enhanced_main.py' in cmdline):
                    
                    if proc.pid != os.getpid():  # Don't kill ourselves
                        print(f"   Stopping process {proc.pid}: {proc.info['name']}")
                        proc.terminate()
                        killed_count += 1
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if killed_count > 0:
            print(f"✅ Stopped {killed_count} agent processes")
        else:
            print("ℹ️ No running agent processes found")
            
    except Exception as e:
        print(f"❌ Error stopping agents: {e}")

def cleanup_system():
    """Cleanup system databases and files"""
    try:
        import os
        import glob
        
        print("🧹 Cleaning up ollama-flow system...")
        
        # Database files to clean
        db_patterns = [
            "*.db",
            "ollama_flow*.db",
            "neural_intelligence.db",
            "sessions.db",
            "monitoring.db",
            "mcp_tools.db"
        ]
        
        cleaned_files = 0
        for pattern in db_patterns:
            for file_path in glob.glob(pattern):
                try:
                    os.remove(file_path)
                    print(f"   Removed: {file_path}")
                    cleaned_files += 1
                except Exception as e:
                    print(f"   Failed to remove {file_path}: {e}")
        
        # Log files
        log_patterns = ["*.log", "ollama_flow*.log"]
        for pattern in log_patterns:
            for file_path in glob.glob(pattern):
                try:
                    os.remove(file_path)
                    print(f"   Removed: {file_path}")
                    cleaned_files += 1
                except Exception as e:
                    print(f"   Failed to remove {file_path}: {e}")
        
        if cleaned_files > 0:
            print(f"✅ Cleaned up {cleaned_files} files")
        else:
            print("ℹ️ No files to clean")
            
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

async def main():
    parser = argparse.ArgumentParser(description="Ollama Flow Framework CLI (Fast Version)")
    parser.add_argument("--task", type=str, help="The task prompt for the orchestrator.")
    parser.add_argument("--project-folder", type=str, help="The project folder path.")
    parser.add_argument("--worker-count", type=int, default=2, help="Number of worker agents.")
    parser.add_argument("--architecture-type", type=str, choices=["HIERARCHICAL", "CENTRALIZED", "FULLY_CONNECTED"], default="CENTRALIZED", help="Architecture type.")
    parser.add_argument("--ollama-model", type=str, default="codellama:7b", help="Ollama model to use.")
    parser.add_argument("--backend", type=str, choices=["ollama"], default="ollama", help="LLM backend to use.")
    parser.add_argument("--config", type=str, help="Path to configuration file.")
    
    # GPU Optimization Parameters
    gpu_group = parser.add_argument_group('GPU Optimization', 'Optional GPU acceleration parameters')
    gpu_group.add_argument("--gpu-enabled", action="store_true", help="Enable GPU acceleration.")
    gpu_group.add_argument("--performance-mode", type=str, choices=["eco", "balanced", "performance", "max"], 
                          default="balanced", help="GPU performance mode.")
    gpu_group.add_argument("--gpu-layers", type=int, help="Number of GPU layers.")
    gpu_group.add_argument("--parallel-requests", type=int, help="Number of parallel GPU requests.")
    gpu_group.add_argument("--gpu-monitoring", action="store_true", help="Enable GPU performance monitoring.")
    gpu_group.add_argument("--auto-scale", action="store_true", help="Enable intelligent auto-scaling.")
    
    # Additional commands
    parser.add_argument("--web-dashboard", action="store_true", help="Launch web dashboard.")
    parser.add_argument("--stop-agents", action="store_true", help="Stop all running agents.")
    parser.add_argument("--cleanup", action="store_true", help="Cleanup databases and files.")
    
    args = parser.parse_args()

    # Handle special commands first
    if args.web_dashboard:
        return await launch_dashboard()
    
    if args.stop_agents:
        return stop_all_agents()
    
    if args.cleanup:
        return cleanup_system()

    try:
        # Initialize configuration
        if args.config:
            config_path = Path(args.config)
            if not config_path.exists():
                print(f"Configuration file not found: {config_path}")
                return
            config = OllamaFlowConfig.from_file(config_path)
        else:
            config = OllamaFlowConfig.from_env()
        
        print(f"Loaded configuration from {config_path if args.config else 'environment'}")
        print(f"Environment: {config.environment}")
        
        # Apply GPU optimizations if requested
        if args.gpu_enabled or args.performance_mode != "balanced" or args.gpu_monitoring:
            setup_gpu_optimizations(args)
        
        # Initialize shared backend manager (single instance)
        backend_manager = EnhancedLLMBackendManager()
        
        # Initialize DB Manager with config
        db_manager = MessageDBManager(
            db_path=config.database.path
        )

        # Check backend availability
        available_backends = await backend_manager.get_available_backends()
        if not available_backends.get('ollama', False):
            print("Error: Ollama backend not available!")
            return
        
        print(f"Using ollama backend")
        
        # Initialize orchestrator with shared backend
        orchestrator = Orchestrator(db_manager)
        orchestrator.backend_manager = backend_manager

        # Get parameters
        worker_count = args.worker_count
        architecture_type = args.architecture_type
        ollama_model = args.ollama_model
        project_folder = args.project_folder or os.getcwd()
        prompt = args.task

        if not prompt:
            print("❌ No task provided. Use --task 'your task description'")
            return

        # Register Queen Agent with shared backend
        queen_agent = QueenAgent("queen-agent-1", "Main Queen", architecture_type, ollama_model)
        queen_agent.backend_manager = backend_manager
        orchestrator.register_agent(queen_agent)

        # Register Worker Agents with shared backend
        if architecture_type == "HIERARCHICAL":
            sub_queen_count = 2
            sub_queen_groups = [[] for _ in range(sub_queen_count)]

            worker_agents = []
            for i in range(worker_count):
                worker = WorkerAgent(f"worker-agent-{i+1}", f"Worker {i+1}", ollama_model, project_folder)
                worker.backend_manager = backend_manager
                worker_agents.append(worker)
                orchestrator.register_agent(worker)
                sub_queen_groups[i % sub_queen_count].append(worker)

            sub_queen_agents = []
            for i in range(sub_queen_count):
                sub_queen = SubQueenAgent(f"sub-queen-{i+1}", f"Sub Queen {chr(65+i)}", ollama_model)
                sub_queen.backend_manager = backend_manager
                sub_queen.initialize_group_agents(sub_queen_groups[i])
                orchestrator.register_agent(sub_queen)
                sub_queen_agents.append(sub_queen)

        elif architecture_type in ["CENTRALIZED", "FULLY_CONNECTED"]:
            for i in range(worker_count):
                worker = WorkerAgent(f"worker-agent-{i+1}", f"Worker {i+1}", ollama_model, project_folder)
                worker.backend_manager = backend_manager
                orchestrator.register_agent(worker)

        # Initialize Queen Agent
        queen_agent.initialize_agents()

        # Start orchestrator polling
        orchestrator.start_polling()

        print("🚀 Ollama Flow Framework (Fast) initialized successfully!")
        print(f"Backend: ollama")
        print(f"Architecture: {architecture_type}")
        print(f"Workers: {worker_count}")
        print(f"Model: {ollama_model}")
        print(f"Project Folder: {project_folder}")

        # Show GPU optimization status
        if args.gpu_enabled or args.performance_mode != "balanced" or args.gpu_monitoring:
            gpu_features = []
            if args.gpu_enabled:
                gpu_features.append("⚡ GPU Acceleration")
            gpu_features.append(f"🎯 {args.performance_mode.title()} Mode")
            if args.gpu_monitoring:
                gpu_features.append("📊 GPU Monitoring")
            if args.auto_scale:
                gpu_features.append("📈 Auto-scaling")
            print(f"GPU Optimization: {', '.join(gpu_features)}")

        response = await orchestrator.run(prompt)
        print(f"\n✅ Final Response from Orchestrator: {response}")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import logging
        logging.exception("Unexpected error in main")
    finally:
        if 'db_manager' in locals():
            db_manager.close()
            print("🔒 Database connection closed.")

if __name__ == "__main__":
    asyncio.run(main())