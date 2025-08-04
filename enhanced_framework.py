#!/usr/bin/env python3
"""
Enhanced Ollama Flow Framework
Includes all fixes for the 5 identified issues:
1. Enhanced database with Redis/in-memory fallback
2. Improved JSON parsing with validation
3. Code generation quality control
4. Comprehensive error handling
5. Graceful shutdown mechanisms
"""

import asyncio
import signal
import sys
import os
import argparse
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional

# Import enhanced components
from enhanced_db_manager import EnhancedDBManager
from orchestrator.orchestrator import Orchestrator
from agents.queen_agent import QueenAgent
from agents.sub_queen_agent import SubQueenAgent
from agents.drone_agent import DroneAgent, DroneRole

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ollama_flow_enhanced.log')
    ]
)
logger = logging.getLogger(__name__)

class EnhancedOllamaFlow:
    """Enhanced Ollama Flow Framework with all fixes applied"""
    
    def __init__(self, 
                 project_folder: str = ".",
                 model: str = "phi3:mini",
                 drone_count: int = 4,
                 architecture: str = "HIERARCHICAL",
                 auto_shutdown: bool = True):
        
        self.project_folder = Path(project_folder).resolve()
        self.model = model
        self.drone_count = drone_count
        self.architecture = architecture
        self.auto_shutdown = auto_shutdown
        
        # Enhanced database manager
        self.db_manager = None
        self.orchestrator = None
        self.agents = {}
        self.shutdown_event = asyncio.Event()
        self.tasks_completed = 0
        
        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()
        
        logger.info(f"🚁 Enhanced Ollama Flow initialized")
        logger.info(f"📁 Project folder: {self.project_folder}")
        logger.info(f"🤖 Model: {self.model}")
        logger.info(f"🔧 Architecture: {self.architecture}")
        logger.info(f"⚡ Auto-shutdown: {self.auto_shutdown}")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"🛑 Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self._graceful_shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def initialize(self):
        """Initialize all components with enhanced error handling"""
        try:
            # Initialize enhanced database
            logger.info("📊 Initializing enhanced database manager...")
            self.db_manager = EnhancedDBManager()
            
            # Show database stats
            stats = self.db_manager.get_stats()
            logger.info(f"✅ Database initialized: {stats}")
            
            # Initialize orchestrator with enhanced DB
            self.orchestrator = Orchestrator(db_manager=self.db_manager)
            
            # Create project folder if it doesn't exist
            self.project_folder.mkdir(parents=True, exist_ok=True)
            
            # Initialize agents based on architecture
            await self._initialize_agents()
            
            logger.info("✅ All components initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            raise
    
    async def _initialize_agents(self):
        """Initialize agents based on selected architecture"""
        try:
            if self.architecture == "HIERARCHICAL":
                await self._setup_hierarchical_architecture()
            elif self.architecture == "CENTRALIZED":
                await self._setup_centralized_architecture()
            elif self.architecture == "FULLY_CONNECTED":
                await self._setup_fully_connected_architecture()
            else:
                raise ValueError(f"Unknown architecture: {self.architecture}")
                
        except Exception as e:
            logger.error(f"❌ Agent initialization failed: {e}")
            raise
    
    async def _setup_hierarchical_architecture(self):
        """Setup hierarchical architecture with Queen and SubQueen agents"""
        logger.info("🏗️ Setting up HIERARCHICAL architecture...")
        
        # Main Queen Agent
        queen = QueenAgent("queen-agent-1", "Main Queen", "HIERARCHICAL", self.model)
        self.agents["queen-agent-1"] = queen
        
        # Create drone agents with different roles
        drone_agents = []
        available_roles = list(DroneRole)
        
        for i in range(self.drone_count):
            role = available_roles[i % len(available_roles)]
            drone_id = f"drone-agent-{i+1}"
            drone_name = f"Drone {i+1} ({role.value})"
            
            drone = DroneAgent(
                agent_id=drone_id,
                name=drone_name,
                model=self.model,
                project_folder_path=str(self.project_folder),
                role=role
            )
            
            drone_agents.append(drone)
            self.agents[drone_id] = drone
            logger.info(f"Created drone agent {i+1} with role: {role.value}")
        
        # Create SubQueen agents
        sub_queens = []
        drones_per_subqueen = max(1, len(drone_agents) // 2)
        
        for i in range(2):  # Create 2 SubQueens
            subqueen_id = f"sub-queen-{i+1}"
            subqueen_name = f"Sub Queen {chr(65+i)}"  # A, B, C...
            
            subqueen = SubQueenAgent(subqueen_id, subqueen_name, self.model)
            
            # Assign drones to this SubQueen
            start_idx = i * drones_per_subqueen
            end_idx = min(start_idx + drones_per_subqueen, len(drone_agents))
            assigned_drones = drone_agents[start_idx:end_idx]
            
            subqueen.initialize_group_agents(assigned_drones)
            sub_queens.append(subqueen)
            self.agents[subqueen_id] = subqueen
        
        # Set orchestrator and initialize Queen (it will find SubQueens automatically)
        queen.set_orchestrator(self.orchestrator)
        
        # Register all agents with orchestrator
        for agent in self.agents.values():
            self.orchestrator.register_agent(agent)
        
        # Initialize queen after all agents are registered
        queen.initialize_agents()
        
        logger.info(f"✅ HIERARCHICAL architecture setup complete")
        logger.info(f"📊 Agents: 1 Queen, {len(sub_queens)} SubQueens, {len(drone_agents)} Drones")
    
    async def _setup_centralized_architecture(self):
        """Setup centralized architecture with direct Queen-to-Drone communication"""
        logger.info("🏗️ Setting up CENTRALIZED architecture...")
        
        # Main Queen Agent
        queen = QueenAgent("queen-agent-1", "Main Queen", "CENTRALIZED", self.model)
        self.agents["queen-agent-1"] = queen
        
        # Create drone agents directly managed by Queen
        drone_agents = []
        available_roles = list(DroneRole)
        
        for i in range(self.drone_count):
            role = available_roles[i % len(available_roles)]
            drone_id = f"drone-agent-{i+1}"
            drone_name = f"Drone {i+1} ({role.value})"
            
            drone = DroneAgent(
                agent_id=drone_id,
                name=drone_name,
                model=self.model,
                project_folder_path=str(self.project_folder),
                role=role
            )
            
            drone_agents.append(drone)
            self.agents[drone_id] = drone
        
        # Register all agents
        for agent in self.agents.values():
            self.orchestrator.register_agent(agent)
        
        # Set orchestrator and initialize queen (it will find drones automatically)
        queen.set_orchestrator(self.orchestrator)
        queen.initialize_agents()
        
        logger.info(f"✅ CENTRALIZED architecture setup complete")
        logger.info(f"📊 Agents: 1 Queen, {len(drone_agents)} Drones")
    
    async def _setup_fully_connected_architecture(self):
        """Setup fully connected architecture where all agents can communicate"""
        logger.info("🏗️ Setting up FULLY_CONNECTED architecture...")
        
        # Create all agents as peers
        available_roles = list(DroneRole)
        
        for i in range(self.drone_count):
            role = available_roles[i % len(available_roles)]
            agent_id = f"agent-{i+1}"
            agent_name = f"Agent {i+1} ({role.value})"
            
            agent = DroneAgent(
                agent_id=agent_id,
                name=agent_name,
                model=self.model,
                project_folder_path=str(self.project_folder),
                role=role
            )
            
            self.agents[agent_id] = agent
        
        # Register all agents
        for agent in self.agents.values():
            self.orchestrator.register_agent(agent)
        
        logger.info(f"✅ FULLY_CONNECTED architecture setup complete")
        logger.info(f"📊 Agents: {len(self.agents)} peer agents")
    
    async def process_task(self, task: str) -> str:
        """Process a task with comprehensive error handling"""
        try:
            logger.info(f"🎯 Processing task: {task[:100]}...")
            
            # Start processing
            start_time = time.time()
            result = await self.orchestrator.run(task)
            processing_time = time.time() - start_time
            
            self.tasks_completed += 1
            
            logger.info(f"✅ Task completed in {processing_time:.2f}s")
            logger.info(f"📊 Total tasks completed: {self.tasks_completed}")
            
            # Auto-shutdown if enabled
            if self.auto_shutdown:
                logger.info("🔄 Auto-shutdown enabled, initiating graceful shutdown...")
                await self._graceful_shutdown()
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Task processing failed: {e}")
            # Don't re-raise, return error info instead
            return f"Task processing failed: {str(e)}"
    
    async def _graceful_shutdown(self):
        """Graceful shutdown with cleanup"""
        try:
            logger.info("🛑 Starting graceful shutdown...")
            
            # Stop all agents
            for agent_id, agent in self.agents.items():
                try:
                    if hasattr(agent, 'stop'):
                        await agent.stop()
                    logger.info(f"✅ Agent {agent_id} stopped")
                except Exception as e:
                    logger.warning(f"⚠️ Error stopping agent {agent_id}: {e}")
            
            # Stop orchestrator
            if self.orchestrator:
                try:
                    if hasattr(self.orchestrator, 'stop'):
                        await self.orchestrator.stop()
                    logger.info("✅ Orchestrator stopped")
                except Exception as e:
                    logger.warning(f"⚠️ Error stopping orchestrator: {e}")
            
            # Cleanup database
            if self.db_manager:
                try:
                    # Clean up old messages
                    cleaned = self.db_manager.cleanup_old_messages(max_age_hours=1)
                    logger.info(f"🧹 Cleaned up {cleaned} old messages")
                    
                    # Close database connections
                    self.db_manager.close()
                    logger.info("✅ Database connections closed")
                except Exception as e:
                    logger.warning(f"⚠️ Error during database cleanup: {e}")
            
            # Final stats
            stats = {
                'tasks_completed': self.tasks_completed,
                'agents_count': len(self.agents),
                'architecture': self.architecture
            }
            logger.info(f"📊 Final statistics: {stats}")
            
        except Exception as e:
            logger.error(f"❌ Error during graceful shutdown: {e}")
        finally:
            self.shutdown_event.set()
            logger.info("✅ Graceful shutdown complete")
    
    async def run_interactive(self):
        """Run interactive mode with continuous task processing"""
        logger.info("🎮 Starting interactive mode...")
        
        try:
            while not self.shutdown_event.is_set():
                try:
                    task = input("\n🎯 Enter task (or 'quit' to exit): ").strip()
                    
                    if task.lower() in ['quit', 'exit', 'q']:
                        break
                    
                    if task:
                        result = await self.process_task(task)
                        print(f"\n✅ Result: {result}")
                    
                except KeyboardInterrupt:
                    break
                except EOFError:
                    break
                except Exception as e:
                    logger.error(f"❌ Interactive mode error: {e}")
                    print(f"❌ Error: {e}")
        
        finally:
            await self._graceful_shutdown()

def create_arg_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Enhanced Ollama Flow - Multi-AI Drone System with fixes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s run "Create a Python OpenCV project for drone image recognition"
  %(prog)s run "Build a web API" --drones 6 --arch CENTRALIZED
  %(prog)s interactive --model llama3 --drones 8
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run a single task')
    run_parser.add_argument('task', help='Task description')
    run_parser.add_argument('--project-folder', default='.', help='Project folder path')
    run_parser.add_argument('--model', default='phi3:mini', help='Ollama model to use')
    run_parser.add_argument('--drones', type=int, default=4, help='Number of drone agents')
    run_parser.add_argument('--arch', choices=['HIERARCHICAL', 'CENTRALIZED', 'FULLY_CONNECTED'], 
                           default='HIERARCHICAL', help='System architecture')
    run_parser.add_argument('--no-auto-shutdown', action='store_true', help='Disable auto-shutdown')
    
    # Interactive command
    interactive_parser = subparsers.add_parser('interactive', help='Run in interactive mode')
    interactive_parser.add_argument('--project-folder', default='.', help='Project folder path')
    interactive_parser.add_argument('--model', default='phi3:mini', help='Ollama model to use')
    interactive_parser.add_argument('--drones', type=int, default=4, help='Number of drone agents')
    interactive_parser.add_argument('--arch', choices=['HIERARCHICAL', 'CENTRALIZED', 'FULLY_CONNECTED'], 
                                   default='HIERARCHICAL', help='System architecture')
    
    return parser

async def main():
    """Main entry point with enhanced error handling"""
    try:
        parser = create_arg_parser()
        args = parser.parse_args()
        
        if not args.command:
            parser.print_help()
            return
        
        # Create enhanced system
        system = EnhancedOllamaFlow(
            project_folder=args.project_folder,
            model=args.model,
            drone_count=args.drones,
            architecture=args.arch,
            auto_shutdown=not getattr(args, 'no_auto_shutdown', False)
        )
        
        # Initialize system
        await system.initialize()
        
        # Execute command
        if args.command == 'run':
            result = await system.process_task(args.task)
            print(f"\n✅ Task Result:\n{result}")
            
        elif args.command == 'interactive':
            await system.run_interactive()
        
    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user")
    except Exception as e:
        logger.error(f"❌ System error: {e}")
        print(f"❌ System error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Handle both direct execution and CLI tool usage
    if len(sys.argv) > 1:
        asyncio.run(main())
    else:
        print("🚁 Enhanced Ollama Flow System")
        print("Usage: python enhanced_framework.py --help")
        print("Or use the ollama-flow CLI tool")