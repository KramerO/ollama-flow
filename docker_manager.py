#!/usr/bin/env python3
"""
Docker Manager for Ollama Flow
Manages Docker container-based agent execution with scaling and orchestration
"""

import asyncio
import logging
import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import docker
from docker.errors import DockerException
import yaml

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DockerManager:
    """Manages Docker containers for AI agent execution"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.docker_client = None
        self.containers = {}
        self.networks = {}
        self.volumes = {}
        self.shutdown_event = asyncio.Event()
        
        # Configuration
        self.image_name = "ollama-flow"
        self.network_name = "ollama-flow-net"
        self.redis_container_name = "ollama-flow-redis"
        
        logger.info(f"Docker Manager initialized for project: {self.project_root}")
    
    async def initialize(self):
        """Initialize Docker client and check Docker availability"""
        try:
            self.docker_client = docker.from_env()
            
            # Test Docker connection
            self.docker_client.ping()
            logger.info("Docker connection established successfully")
            
            # Get Docker info
            docker_info = self.docker_client.info()
            logger.info(f"Docker version: {docker_info.get('ServerVersion', 'unknown')}")
            
        except DockerException as e:
            logger.error(f"Docker initialization failed: {e}")
            raise
    
    async def build_images(self, rebuild: bool = False):
        """Build Docker images for Ollama Flow"""
        try:
            logger.info("Building Docker images...")
            
            # Build main image
            if rebuild or not self._image_exists(self.image_name):
                logger.info(f"Building main image: {self.image_name}")
                image, logs = self.docker_client.images.build(
                    path=str(self.project_root),
                    tag=self.image_name,
                    rm=True,
                    nocache=rebuild
                )
                
                # Log build output
                for log in logs:
                    if 'stream' in log:
                        logger.info(log['stream'].strip())
                
                logger.info(f"Successfully built image: {self.image_name}")
            else:
                logger.info(f"Using existing image: {self.image_name}")
            
            # Build development image
            dev_image_name = f"{self.image_name}-dev"
            if rebuild or not self._image_exists(dev_image_name):
                logger.info(f"Building development image: {dev_image_name}")
                image, logs = self.docker_client.images.build(
                    path=str(self.project_root),
                    dockerfile="Dockerfile.dev",
                    tag=dev_image_name,
                    rm=True,
                    nocache=rebuild
                )
                logger.info(f"Successfully built development image: {dev_image_name}")
            
        except DockerException as e:
            logger.error(f"Failed to build Docker images: {e}")
            raise
    
    def _image_exists(self, image_name: str) -> bool:
        """Check if a Docker image exists"""
        try:
            self.docker_client.images.get(image_name)
            return True
        except docker.errors.ImageNotFound:
            return False
    
    async def create_network(self):
        """Create Docker network for inter-container communication"""
        try:
            # Check if network already exists
            try:
                network = self.docker_client.networks.get(self.network_name)
                logger.info(f"Using existing network: {self.network_name}")
                self.networks[self.network_name] = network
                return network
            except docker.errors.NotFound:
                pass
            
            # Create new network
            logger.info(f"Creating Docker network: {self.network_name}")
            network = self.docker_client.networks.create(
                self.network_name,
                driver="bridge",
                ipam=docker.types.IPAMConfig(
                    driver="default",
                    pool_configs=[
                        docker.types.IPAMPool(subnet="172.20.0.0/16")
                    ]
                )
            )
            
            self.networks[self.network_name] = network
            logger.info(f"Created network: {self.network_name}")
            return network
            
        except DockerException as e:
            logger.error(f"Failed to create network: {e}")
            raise
    
    async def start_redis(self):
        """Start Redis container for enhanced database"""
        try:
            # Check if Redis container already exists
            existing_container = self._get_container(self.redis_container_name)
            if existing_container:
                if existing_container.status != "running":
                    logger.info("Starting existing Redis container...")
                    existing_container.start()
                else:
                    logger.info("Redis container already running")
                self.containers[self.redis_container_name] = existing_container
                return existing_container
            
            logger.info("Starting Redis container...")
            
            # Create volume for Redis data persistence
            volume_name = "ollama-flow-redis-data"
            try:
                volume = self.docker_client.volumes.get(volume_name)
            except docker.errors.NotFound:
                volume = self.docker_client.volumes.create(volume_name)
                logger.info(f"Created volume: {volume_name}")
            
            # Start Redis container
            container = self.docker_client.containers.run(
                "redis:7.2-alpine",
                name=self.redis_container_name,
                ports={'6379/tcp': 6379},
                volumes={volume_name: {'bind': '/data', 'mode': 'rw'}},
                command="redis-server --appendonly yes",
                network=self.network_name,
                detach=True,
                restart_policy={"Name": "unless-stopped"},
                healthcheck={
                    "test": ["CMD", "redis-cli", "ping"],
                    "interval": 10_000_000_000,  # 10s in nanoseconds
                    "timeout": 5_000_000_000,    # 5s in nanoseconds
                    "retries": 3
                }
            )
            
            self.containers[self.redis_container_name] = container
            logger.info(f"Redis container started: {container.id[:12]}")
            
            # Wait for Redis to be healthy
            await self._wait_for_container_health(container)
            
            return container
            
        except DockerException as e:
            logger.error(f"Failed to start Redis container: {e}")
            raise
    
    async def start_main_app(self, port: int = 8080):
        """Start main Ollama Flow application container"""
        try:
            container_name = "ollama-flow-app"
            
            # Check if container already exists
            existing_container = self._get_container(container_name)
            if existing_container:
                if existing_container.status != "running":
                    existing_container.start()
                else:
                    logger.info("Main app container already running")
                self.containers[container_name] = existing_container
                return existing_container
            
            logger.info("Starting main application container...")
            
            # Create necessary volumes
            data_volume = self._ensure_volume("ollama-flow-data")
            logs_volume = self._ensure_volume("ollama-flow-logs")
            
            # Environment variables
            environment = {
                'PYTHONUNBUFFERED': '1',
                'REDIS_HOST': self.redis_container_name,
                'REDIS_PORT': '6379',
                'OLLAMA_HOST': 'host.docker.internal:11434',
                'DOCKER_MODE': 'true'
            }
            
            # Start main app container
            container = self.docker_client.containers.run(
                self.image_name,
                name=container_name,
                ports={f'{port}/tcp': port},
                environment=environment,
                volumes={
                    data_volume.name: {'bind': '/app/data', 'mode': 'rw'},
                    logs_volume.name: {'bind': '/app/logs', 'mode': 'rw'},
                    str(self.project_root / "output"): {'bind': '/app/output', 'mode': 'rw'}
                },
                network=self.network_name,
                detach=True,
                restart_policy={"Name": "unless-stopped"}
            )
            
            self.containers[container_name] = container
            logger.info(f"Main app container started: {container.id[:12]}")
            
            return container
            
        except DockerException as e:
            logger.error(f"Failed to start main app container: {e}")
            raise
    
    async def start_agent_drones(self, count: int = 4):
        """Start specified number of agent drone containers"""
        try:
            logger.info(f"Starting {count} agent drone containers...")
            
            drones = []
            for i in range(1, count + 1):
                drone = await self._start_agent_drone(i)
                drones.append(drone)
            
            logger.info(f"Successfully started {len(drones)} agent drones")
            return drones
            
        except DockerException as e:
            logger.error(f"Failed to start agent drones: {e}")
            raise
    
    async def _start_agent_drone(self, drone_id: int):
        """Start a single agent drone container"""
        container_name = f"ollama-flow-drone-{drone_id}"
        
        # Check if drone already exists
        existing_container = self._get_container(container_name)
        if existing_container:
            if existing_container.status != "running":
                existing_container.start()
            else:
                logger.info(f"Drone {drone_id} already running")
            self.containers[container_name] = existing_container
            return existing_container
        
        # Environment for this drone
        environment = {
            'PYTHONUNBUFFERED': '1',
            'REDIS_HOST': self.redis_container_name,
            'REDIS_PORT': '6379',
            'OLLAMA_HOST': 'host.docker.internal:11434',
            'DOCKER_MODE': 'true',
            'AGENT_MODE': 'drone',
            'DRONE_ID': str(drone_id)
        }
        
        # Create volumes
        data_volume = self._ensure_volume("ollama-flow-data")
        logs_volume = self._ensure_volume("ollama-flow-logs")
        
        # Start drone container
        container = self.docker_client.containers.run(
            self.image_name,
            name=container_name,
            environment=environment,
            volumes={
                data_volume.name: {'bind': '/app/data', 'mode': 'rw'},
                logs_volume.name: {'bind': '/app/logs', 'mode': 'rw'}
            },
            network=self.network_name,
            command=["python3", "agents/docker_drone_agent.py"],
            detach=True,
            restart_policy={"Name": "unless-stopped"}
        )
        
        self.containers[container_name] = container
        logger.info(f"Agent drone {drone_id} started: {container.id[:12]}")
        
        return container
    
    def _get_container(self, name: str):
        """Get existing container by name"""
        try:
            return self.docker_client.containers.get(name)
        except docker.errors.NotFound:
            return None
    
    def _ensure_volume(self, volume_name: str):
        """Ensure a Docker volume exists"""
        try:
            return self.docker_client.volumes.get(volume_name)
        except docker.errors.NotFound:
            volume = self.docker_client.volumes.create(volume_name)
            logger.info(f"Created volume: {volume_name}")
            return volume
    
    async def _wait_for_container_health(self, container, timeout: int = 60):
        """Wait for container to become healthy"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            container.reload()
            
            if hasattr(container.attrs, 'State') and 'Health' in container.attrs['State']:
                health_status = container.attrs['State']['Health']['Status']
                if health_status == 'healthy':
                    logger.info(f"Container {container.name} is healthy")
                    return True
                elif health_status == 'unhealthy':
                    raise Exception(f"Container {container.name} became unhealthy")
            
            # If no health check, just check if running
            if container.status == 'running':
                await asyncio.sleep(2)  # Give it a moment to start properly
                return True
            
            await asyncio.sleep(1)
        
        raise Exception(f"Container {container.name} failed to become healthy within {timeout}s")
    
    async def scale_drones(self, target_count: int):
        """Scale agent drones to target count"""
        try:
            current_drones = [name for name in self.containers.keys() 
                            if name.startswith("ollama-flow-drone-")]
            current_count = len(current_drones)
            
            logger.info(f"Scaling drones from {current_count} to {target_count}")
            
            if target_count > current_count:
                # Scale up
                for i in range(current_count + 1, target_count + 1):
                    await self._start_agent_drone(i)
            elif target_count < current_count:
                # Scale down
                for i in range(target_count + 1, current_count + 1):
                    await self._stop_agent_drone(i)
            
            logger.info(f"Successfully scaled to {target_count} drones")
            
        except Exception as e:
            logger.error(f"Failed to scale drones: {e}")
            raise
    
    async def _stop_agent_drone(self, drone_id: int):
        """Stop a specific agent drone"""
        container_name = f"ollama-flow-drone-{drone_id}"
        
        if container_name in self.containers:
            container = self.containers[container_name]
            logger.info(f"Stopping drone {drone_id}...")
            container.stop(timeout=30)
            container.remove()
            del self.containers[container_name]
            logger.info(f"Drone {drone_id} stopped and removed")
    
    async def stop_all(self):
        """Stop all managed containers"""
        try:
            logger.info("Stopping all containers...")
            
            for name, container in list(self.containers.items()):
                try:
                    logger.info(f"Stopping container: {name}")
                    container.stop(timeout=30)
                    container.remove()
                except Exception as e:
                    logger.error(f"Error stopping container {name}: {e}")
            
            self.containers.clear()
            logger.info("All containers stopped")
            
        except Exception as e:
            logger.error(f"Error stopping containers: {e}")
    
    async def cleanup(self):
        """Cleanup all resources"""
        try:
            await self.stop_all()
            
            # Remove network
            if self.network_name in self.networks:
                try:
                    self.networks[self.network_name].remove()
                    logger.info(f"Removed network: {self.network_name}")
                except Exception as e:
                    logger.error(f"Error removing network: {e}")
            
            # Close Docker client
            if self.docker_client:
                self.docker_client.close()
            
            logger.info("Docker cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def get_container_logs(self, container_name: str, tail: int = 50) -> str:
        """Get logs from a specific container"""
        if container_name in self.containers:
            container = self.containers[container_name]
            return container.logs(tail=tail).decode('utf-8')
        return f"Container {container_name} not found"
    
    def get_container_stats(self) -> Dict[str, Any]:
        """Get statistics for all managed containers"""
        stats = {}
        for name, container in self.containers.items():
            try:
                container.reload()
                stats[name] = {
                    'status': container.status,
                    'id': container.id[:12],
                    'image': container.image.tags[0] if container.image.tags else 'unknown'
                }
            except Exception as e:
                stats[name] = {'error': str(e)}
        
        return stats

# Command-line interface
async def main():
    """Main CLI for Docker Manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ollama Flow Docker Manager')
    parser.add_argument('--build', action='store_true', help='Build Docker images')
    parser.add_argument('--rebuild', action='store_true', help='Rebuild Docker images')
    parser.add_argument('--start', action='store_true', help='Start all services')
    parser.add_argument('--stop', action='store_true', help='Stop all services')
    parser.add_argument('--scale', type=int, help='Scale workers to specified count')
    parser.add_argument('--logs', type=str, help='Show logs for container')
    parser.add_argument('--stats', action='store_true', help='Show container statistics')
    
    args = parser.parse_args()
    
    manager = DockerManager()
    
    try:
        await manager.initialize()
        
        if args.build or args.rebuild:
            await manager.build_images(rebuild=args.rebuild)
        
        if args.start:
            await manager.create_network()
            await manager.start_redis()
            await manager.start_main_app()
            await manager.start_agent_drones()
        
        if args.scale is not None:
            await manager.scale_drones(args.scale)
        
        if args.logs:
            logs = manager.get_container_logs(args.logs)
            print(logs)
        
        if args.stats:
            stats = manager.get_container_stats()
            for name, stat in stats.items():
                print(f"{name}: {stat}")
        
        if args.stop:
            await manager.stop_all()
    
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
    finally:
        await manager.cleanup()
    
    return 0

if __name__ == "__main__":
    exit(asyncio.run(main()))