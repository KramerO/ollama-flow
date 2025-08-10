#!/usr/bin/env python3
"""
Docker Drone Agent - Containerized AI Agent Execution
Specialized drone for running agents in Docker containers
"""

import os
import sys
import asyncio
import logging
import signal
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

from enhanced_db_manager import EnhancedDBManager
from agents.drone_agent import DroneAgent, DroneRole
from agents.base_agent import AgentMessage

# Configure logging for container environment
logging.basicConfig(
    level=logging.DEBUG if os.getenv('DEBUG_MODE') == 'true' else logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/logs/docker_agent.log')
    ]
)
logger = logging.getLogger(__name__)

class DockerDroneAgent:
    """Docker-optimized drone agent for containerized execution"""
    
    def __init__(self, drone_id: int = 1):
        self.drone_id = drone_id
        self.agent_id = f"docker_drone_{drone_id}"
        self.shutdown_event = asyncio.Event()
        self.agent = None
        self.db_manager = None
        
        # Docker environment configuration
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', 6379))
        self.ollama_host = os.getenv('OLLAMA_HOST', 'localhost:11434')
        
        logger.info(f"Docker Drone Agent {drone_id} initializing...")
        logger.info(f"Redis: {self.redis_host}:{self.redis_port}")
        logger.info(f"Ollama: {self.ollama_host}")
        
    async def initialize(self):
        """Initialize the Docker drone agent"""
        try:
            # Initialize enhanced database manager with Redis connection
            self.db_manager = EnhancedDBManager(
                redis_host=self.redis_host,
                redis_port=self.redis_port,
                fallback_to_memory=True
            )
            
            # Wait for Redis connection
            await self._wait_for_redis()
            
            # Determine agent role based on drone ID
            roles = [DroneRole.ANALYST, DroneRole.DATA_SCIENTIST, 
                    DroneRole.IT_ARCHITECT, DroneRole.DEVELOPER]
            role = roles[self.drone_id % len(roles)]
            
            # Create specialized drone agent
            self.agent = DroneAgent(
                agent_id=self.agent_id,
                name=f"DockerDrone_{self.drone_id}_{role.value}",
                role=role,
                model="phi3:mini"  # Light model for container efficiency
            )
            
            # Configure agent with Docker-specific settings
            self.agent.set_db_manager(self.db_manager)
            self.agent.docker_mode = True
            self.agent.ollama_host = self.ollama_host
            
            logger.info(f"Docker Drone Agent {self.drone_id} initialized successfully")
            logger.info(f"Agent Role: {role.value}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Docker Drone Agent: {e}")
            raise
    
    async def _wait_for_redis(self, max_retries: int = 30):
        """Wait for Redis to be available"""
        for i in range(max_retries):
            try:
                if await self.db_manager.test_connection():
                    logger.info("Redis connection established")
                    return
            except Exception as e:
                logger.warning(f"Redis connection attempt {i+1}/{max_retries} failed: {e}")
                await asyncio.sleep(2)
        
        raise Exception("Failed to connect to Redis after maximum retries")
    
    async def run(self):
        """Main drone execution loop"""
        try:
            await self.initialize()
            
            logger.info(f"Docker Drone Agent {self.drone_id} starting main loop...")
            
            # Register drone as available
            await self._register_drone()
            
            # Main execution loop
            while not self.shutdown_event.is_set():
                try:
                    # Check for assigned tasks
                    await self._process_assigned_tasks()
                    
                    # Heartbeat to indicate worker is alive
                    await self._send_heartbeat()
                    
                    # Sleep briefly to prevent excessive CPU usage
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    await asyncio.sleep(5)  # Wait longer on error
            
        except Exception as e:
            logger.error(f"Fatal error in Docker Drone Agent: {e}")
            raise
        finally:
            await self._cleanup()
    
    async def _register_drone(self):
        """Register this drone as available in the database"""
        try:
            drone_info = {
                'drone_id': self.drone_id,
                'agent_id': self.agent_id,
                'role': self.agent.role.value if self.agent else 'unknown',
                'status': 'available',
                'container_id': os.getenv('HOSTNAME', 'unknown'),
                'last_seen': time.time()
            }
            
            # Store drone registration in database
            self.db_manager.store_drone_info(self.agent_id, drone_info)
            logger.info(f"Drone {self.drone_id} registered successfully")
            
        except Exception as e:
            logger.error(f"Failed to register drone: {e}")
    
    async def _process_assigned_tasks(self):
        """Process any tasks assigned to this drone"""
        try:
            # Check for direct messages to this agent
            if self.agent and hasattr(self.agent, '_message_polling_task'):
                # Agent's built-in message processing handles this
                pass
            
            # Check for general drone tasks
            tasks = self.db_manager.get_drone_tasks(self.agent_id)
            for task in tasks:
                await self._execute_task(task)
                
        except Exception as e:
            logger.error(f"Error processing assigned tasks: {e}")
    
    async def _execute_task(self, task: Dict[str, Any]):
        """Execute a specific task assigned to this drone"""
        try:
            logger.info(f"Executing task: {task.get('id', 'unknown')}")
            
            task_type = task.get('type', '')
            task_data = task.get('data', {})
            
            if task_type == 'process_subtask':
                # Handle subtask processing
                await self._process_subtask(task_data)
            elif task_type == 'code_generation':
                # Handle code generation task
                await self._generate_code(task_data)
            else:
                logger.warning(f"Unknown task type: {task_type}")
            
            # Mark task as completed
            self.db_manager.mark_task_completed(task.get('id'))
            
        except Exception as e:
            logger.error(f"Error executing task {task.get('id')}: {e}")
            self.db_manager.mark_task_failed(task.get('id'), str(e))
    
    async def _process_subtask(self, task_data: Dict[str, Any]):
        """Process a subtask using the agent"""
        if not self.agent:
            raise Exception("Agent not initialized")
        
        subtask = task_data.get('subtask', '')
        context = task_data.get('context', {})
        
        # Use agent to process the subtask
        result = await self.agent.process_task(subtask, context)
        
        # Store result in database
        self.db_manager.store_task_result(task_data.get('id'), result)
        
        logger.info(f"Subtask processed successfully: {subtask[:50]}...")
    
    async def _generate_code(self, task_data: Dict[str, Any]):
        """Generate code for a specific task"""
        if not self.agent:
            raise Exception("Agent not initialized")
        
        description = task_data.get('description', '')
        requirements = task_data.get('requirements', [])
        
        # Use agent to generate code
        result = await self.agent.generate_code(description, requirements)
        
        # Store result in database
        self.db_manager.store_code_result(task_data.get('id'), result)
        
        logger.info(f"Code generated successfully for: {description[:50]}...")
    
    async def _send_heartbeat(self):
        """Send heartbeat to indicate drone is alive"""
        try:
            heartbeat_data = {
                'drone_id': self.drone_id,
                'agent_id': self.agent_id,
                'timestamp': time.time(),
                'status': 'active',
                'container_id': os.getenv('HOSTNAME', 'unknown')
            }
            
            self.db_manager.store_drone_heartbeat(self.agent_id, heartbeat_data)
            
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")
    
    async def _cleanup(self):
        """Cleanup resources before shutdown"""
        try:
            logger.info(f"Docker Drone Agent {self.drone_id} cleaning up...")
            
            # Mark drone as shutting down
            if self.db_manager:
                self.db_manager.update_drone_status(self.agent_id, 'shutting_down')
            
            # Stop agent polling if active
            if self.agent and hasattr(self.agent, 'polling_task'):
                if self.agent.polling_task:
                    self.agent.polling_task.cancel()
            
            # Close database connections
            if self.db_manager:
                await self.db_manager.close()
            
            logger.info(f"Docker Drone Agent {self.drone_id} cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def handle_shutdown(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received shutdown signal {signum}")
        self.shutdown_event.set()

async def main():
    """Main entry point for Docker Drone Agent"""
    # Get drone ID from environment
    drone_id = int(os.getenv('DRONE_ID', 1))
    
    # Create and run drone
    drone = DockerDroneAgent(drone_id)
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, drone.handle_shutdown)
    signal.signal(signal.SIGTERM, drone.handle_shutdown)
    
    try:
        await drone.run()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Run the drone
    asyncio.run(main())