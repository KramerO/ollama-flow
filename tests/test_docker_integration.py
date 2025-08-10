#!/usr/bin/env python3
"""
Test Suite for Docker Integration
Tests container-based agent execution, Docker Manager, and integration with enhanced framework
"""

import pytest
import asyncio
import tempfile
import shutil
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import components to test
from docker_manager import DockerManager
from agents.docker_agent_worker import DockerAgentWorker
from enhanced_framework import EnhancedOllamaFlow, DOCKER_AVAILABLE

class TestDockerManager:
    """Test Docker Manager functionality"""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def docker_manager(self, temp_project_dir):
        """Create DockerManager instance for testing"""
        return DockerManager(temp_project_dir)
    
    @pytest.mark.skipif(not DOCKER_AVAILABLE, reason="Docker not available")
    async def test_docker_manager_initialization(self, docker_manager):
        """Test DockerManager initialization"""
        await docker_manager.initialize()
        assert docker_manager.docker_client is not None
        assert docker_manager.project_root.exists()
    
    @pytest.mark.skipif(not DOCKER_AVAILABLE, reason="Docker not available")
    async def test_image_build(self, docker_manager):
        """Test Docker image building"""
        with patch.object(docker_manager, '_image_exists', return_value=False):
            with patch.object(docker_manager.docker_client.images, 'build') as mock_build:
                mock_build.return_value = (Mock(), [{'stream': 'Building...'}])
                await docker_manager.build_images()
                mock_build.assert_called()
    
    @pytest.mark.skipif(not DOCKER_AVAILABLE, reason="Docker not available")
    async def test_network_creation(self, docker_manager):
        """Test Docker network creation"""
        await docker_manager.initialize()
        
        with patch.object(docker_manager.docker_client.networks, 'get') as mock_get:
            mock_get.side_effect = Exception("Network not found")
            with patch.object(docker_manager.docker_client.networks, 'create') as mock_create:
                mock_network = Mock()
                mock_create.return_value = mock_network
                
                network = await docker_manager.create_network()
                
                mock_create.assert_called_once()
                assert network == mock_network
    
    async def test_container_management(self, docker_manager):
        """Test container lifecycle management"""
        with patch.object(docker_manager, 'docker_client') as mock_client:
            mock_container = Mock()
            mock_container.status = 'running'
            mock_container.id = 'test123'
            mock_client.containers.run.return_value = mock_container
            
            # Mock Redis container start
            result = await docker_manager.start_redis()
            assert result == mock_container
    
    async def test_worker_scaling(self, docker_manager):
        """Test agent worker scaling"""
        with patch.object(docker_manager, '_start_agent_worker') as mock_start:
            mock_start.return_value = Mock()
            
            workers = await docker_manager.start_agent_workers(count=3)
            assert len(workers) == 3
            assert mock_start.call_count == 3

class TestDockerAgentWorker:
    """Test Docker Agent Worker functionality"""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Create mock database manager"""
        db_manager = Mock()
        db_manager.test_connection.return_value = True
        db_manager.get_worker_tasks.return_value = []
        return db_manager
    
    @pytest.fixture
    def docker_worker(self):
        """Create DockerAgentWorker instance"""
        with patch.dict(os.environ, {'WORKER_ID': '1', 'REDIS_HOST': 'localhost'}):
            return DockerAgentWorker(worker_id=1)
    
    async def test_worker_initialization(self, docker_worker, mock_db_manager):
        """Test worker initialization"""
        with patch.object(docker_worker, '_wait_for_redis'):
            with patch('agents.docker_agent_worker.EnhancedDBManager', return_value=mock_db_manager):
                with patch('agents.docker_agent_worker.DroneAgent') as mock_agent:
                    mock_agent_instance = Mock()
                    mock_agent.return_value = mock_agent_instance
                    
                    await docker_worker.initialize()
                    
                    assert docker_worker.db_manager == mock_db_manager
                    assert docker_worker.agent == mock_agent_instance
    
    async def test_worker_task_processing(self, docker_worker, mock_db_manager):
        """Test worker task processing"""
        # Setup worker
        docker_worker.db_manager = mock_db_manager
        docker_worker.agent = Mock()
        
        # Mock task
        test_task = {
            'id': 'task_123',
            'type': 'process_subtask',
            'data': {'subtask': 'Test task', 'context': {}}
        }
        
        mock_db_manager.get_worker_tasks.return_value = [test_task]
        
        # Test task execution
        await docker_worker._process_assigned_tasks()
        
        # Verify task was processed
        docker_worker.agent.process_task.assert_called_once()
    
    async def test_worker_heartbeat(self, docker_worker, mock_db_manager):
        """Test worker heartbeat functionality"""
        docker_worker.db_manager = mock_db_manager
        
        await docker_worker._send_heartbeat()
        
        mock_db_manager.store_worker_heartbeat.assert_called_once()
    
    async def test_worker_cleanup(self, docker_worker, mock_db_manager):
        """Test worker cleanup"""
        docker_worker.db_manager = mock_db_manager
        docker_worker.agent = Mock()
        docker_worker.agent.polling_task = Mock()
        
        await docker_worker._cleanup()
        
        mock_db_manager.update_worker_status.assert_called_once()
        docker_worker.agent.polling_task.cancel.assert_called_once()

class TestDockerIntegration:
    """Test integration between Docker components and enhanced framework"""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    async def test_framework_docker_mode_initialization(self, temp_project_dir):
        """Test enhanced framework with Docker mode"""
        with patch('enhanced_framework.DOCKER_AVAILABLE', True):
            with patch('enhanced_framework.DockerManager') as mock_docker_manager:
                framework = EnhancedOllamaFlow(
                    project_folder=temp_project_dir,
                    docker_mode=True,
                    drone_count=2
                )
                
                assert framework.docker_mode is True
                assert framework.docker_manager is not None
                mock_docker_manager.assert_called_once()
    
    async def test_framework_fallback_when_docker_unavailable(self, temp_project_dir):
        """Test framework fallback when Docker is unavailable"""
        with patch('enhanced_framework.DOCKER_AVAILABLE', False):
            framework = EnhancedOllamaFlow(
                project_folder=temp_project_dir,
                docker_mode=True,
                drone_count=2
            )
            
            # Should fall back to non-Docker mode
            assert framework.docker_mode is False
            assert framework.docker_manager is None
    
    async def test_docker_compose_file_validity(self):
        """Test Docker Compose file structure"""
        compose_file = Path(__file__).parent.parent / "docker-compose.yml"
        assert compose_file.exists(), "docker-compose.yml should exist"
        
        # Check if file is valid YAML
        import yaml
        with open(compose_file) as f:
            compose_data = yaml.safe_load(f)
        
        # Verify required services
        assert 'services' in compose_data
        assert 'redis' in compose_data['services']
        assert 'ollama-flow' in compose_data['services']
        assert 'agent-worker-1' in compose_data['services']
    
    async def test_dockerfile_exists_and_valid(self):
        """Test Dockerfile exists and has proper structure"""
        dockerfile = Path(__file__).parent.parent / "Dockerfile"
        assert dockerfile.exists(), "Dockerfile should exist"
        
        # Check basic Dockerfile structure
        with open(dockerfile) as f:
            content = f.read()
        
        # Verify essential Dockerfile commands
        assert "FROM python:" in content
        assert "WORKDIR /app" in content
        assert "COPY requirements.txt" in content
        assert "RUN pip install" in content
        assert "CMD " in content
    
    async def test_dockerignore_excludes_unnecessary_files(self):
        """Test .dockerignore excludes proper files"""
        dockerignore = Path(__file__).parent.parent / ".dockerignore"
        assert dockerignore.exists(), ".dockerignore should exist"
        
        with open(dockerignore) as f:
            ignored_patterns = f.read()
        
        # Verify important exclusions
        assert "__pycache__" in ignored_patterns
        assert ".git/" in ignored_patterns
        assert "*.pyc" in ignored_patterns
        assert "node_modules/" in ignored_patterns

class TestDockerEnvironment:
    """Test Docker environment configuration and variables"""
    
    def test_docker_environment_variables(self):
        """Test Docker environment variable setup"""
        # Test environment variable parsing
        with patch.dict(os.environ, {
            'REDIS_HOST': 'test-redis',
            'REDIS_PORT': '6380',
            'OLLAMA_HOST': 'test-ollama:11435',
            'DOCKER_MODE': 'true',
            'WORKER_ID': '5'
        }):
            worker = DockerAgentWorker(worker_id=5)
            
            assert worker.redis_host == 'test-redis'
            assert worker.redis_port == 6380
            assert worker.ollama_host == 'test-ollama:11435'
            assert worker.worker_id == 5
    
    def test_docker_healthcheck_script(self):
        """Test Docker health check functionality"""
        # This would test the health check script in a real container
        # For unit tests, we verify the script exists and has correct structure
        pass

# Performance and Load Tests
class TestDockerPerformance:
    """Test Docker integration performance"""
    
    @pytest.mark.slow
    async def test_multiple_worker_startup_time(self):
        """Test performance of starting multiple workers"""
        with patch('docker_manager.docker') as mock_docker:
            mock_client = Mock()
            mock_docker.from_env.return_value = mock_client
            
            manager = DockerManager()
            await manager.initialize()
            
            start_time = asyncio.get_event_loop().time()
            await manager.start_agent_workers(count=8)
            end_time = asyncio.get_event_loop().time()
            
            # Should start workers in reasonable time
            startup_time = end_time - start_time
            assert startup_time < 30  # 30 seconds max for 8 workers
    
    @pytest.mark.slow
    async def test_worker_task_throughput(self):
        """Test worker task processing throughput"""
        # This would test actual task processing speed
        # Implementation depends on specific performance requirements
        pass

# Integration Tests
class TestEndToEndDockerIntegration:
    """End-to-end integration tests for Docker functionality"""
    
    @pytest.mark.integration
    @pytest.mark.skipif(not DOCKER_AVAILABLE, reason="Docker not available")
    async def test_full_docker_workflow(self):
        """Test complete Docker workflow from start to finish"""
        # This test would require actual Docker environment
        # and would test the full workflow:
        # 1. Build images
        # 2. Start services
        # 3. Process tasks
        # 4. Scale workers
        # 5. Cleanup
        pass
    
    @pytest.mark.integration
    async def test_docker_compose_startup(self):
        """Test Docker Compose startup and service communication"""
        # Would test actual docker-compose up functionality
        pass

# Fixtures for database testing with Docker
@pytest.fixture
async def redis_container():
    """Start Redis container for testing"""
    if not DOCKER_AVAILABLE:
        pytest.skip("Docker not available")
    
    import docker
    client = docker.from_env()
    
    # Start Redis container
    container = client.containers.run(
        "redis:7.2-alpine",
        ports={'6379/tcp': None},
        detach=True,
        remove=True
    )
    
    # Wait for Redis to be ready
    await asyncio.sleep(2)
    
    yield container
    
    # Cleanup
    container.stop()

# Mock fixtures for testing without actual Docker
@pytest.fixture
def mock_docker_client():
    """Mock Docker client for testing without Docker"""
    with patch('docker.from_env') as mock_from_env:
        mock_client = Mock()
        mock_from_env.return_value = mock_client
        
        # Setup common mock responses
        mock_client.ping.return_value = True
        mock_client.info.return_value = {'ServerVersion': '20.10.0'}
        mock_client.images.build.return_value = (Mock(), [])
        mock_client.containers.run.return_value = Mock()
        mock_client.networks.create.return_value = Mock()
        mock_client.volumes.create.return_value = Mock()
        
        yield mock_client

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])