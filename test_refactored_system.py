#!/usr/bin/env python3
"""
Comprehensive test suite for the refactored ollama-flow system
Tests all major components: config, exceptions, backends, agents
"""
import pytest
import asyncio
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import refactored components
from exceptions import (
    OllamaFlowException, BackendException, BackendUnavailableException,
    AgentException, TaskDecompositionException, ConfigurationException
)
from config import (
    OllamaFlowConfig, BackendConfig, DatabaseConfig, AgentConfig,
    SecurityConfig, LoggingConfig, PerformanceConfig
)
from llm_backend import (
    EnhancedLLMBackendManager, LLMResponse, BackendStatus,
    BackendMetrics, BackendHealth
)
from agents.mixins import (
    TaskDecompositionMixin, MessageHandlingMixin, 
    PerformanceTrackingMixin, ValidationMixin
)


class TestExceptions:
    """Test custom exception hierarchy"""
    
    def test_base_exception(self):
        """Test base OllamaFlowException"""
        exc = OllamaFlowException("Test error", {"key": "value"})
        assert str(exc) == "Test error (Details: {'key': 'value'})"
        assert exc.message == "Test error"
        assert exc.details == {"key": "value"}
    
    def test_backend_exception_hierarchy(self):
        """Test backend exception inheritance"""
        exc = BackendUnavailableException("Backend down")
        assert isinstance(exc, BackendException)
        assert isinstance(exc, OllamaFlowException)
        assert str(exc) == "Backend down"
    
    def test_agent_exception_hierarchy(self):
        """Test agent exception inheritance"""
        exc = TaskDecompositionException("Decomposition failed")
        assert isinstance(exc, AgentException)
        assert isinstance(exc, OllamaFlowException)


class TestConfiguration:
    """Test configuration management system"""
    
    def test_default_config_creation(self):
        """Test creating default configuration"""
        config = OllamaFlowConfig()
        
        assert config.default_backend == "ollama"
        assert config.environment == "development"
        assert config.database.path == "ollama_flow_messages.db"
        assert config.agents.default_model == "llama3"
        assert config.security.enable_sandboxing is True
        assert "ollama" in config.backends
    
    def test_config_from_env(self):
        """Test loading configuration from environment variables"""
        with patch.dict(os.environ, {
            'OLLAMA_BACKEND': 'zluda',
            'OLLAMA_MODEL': 'codellama:7b',
            'OLLAMA_WORKER_COUNT': '8',
            'OLLAMA_LOG_LEVEL': 'DEBUG'
        }):
            config = OllamaFlowConfig.from_env()
            
            assert config.default_backend == "zluda"
            assert config.agents.default_model == "codellama:7b"
            assert config.agents.max_workers == 8
            assert config.logging.level == "DEBUG"
    
    def test_config_validation(self):
        """Test configuration validation"""
        config = OllamaFlowConfig()
        issues = config.validate()
        
        # Should have no issues with default config
        assert len(issues) == 0
        
        # Test invalid configuration
        config.backends = {}  # No backends
        issues = config.validate()
        assert len(issues) > 0
        assert any("No backends configured" in issue for issue in issues)
    
    def test_config_save_load(self):
        """Test saving and loading configuration"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = Path(f.name)
        
        try:
            # Create and save config
            original_config = OllamaFlowConfig()
            original_config.default_backend = "zluda"
            original_config.agents.max_workers = 6
            original_config.save_to_file(config_path)
            
            # Load config
            loaded_config = OllamaFlowConfig.from_file(config_path)
            
            assert loaded_config.default_backend == "zluda"
            assert loaded_config.agents.max_workers == 6
            
        finally:
            config_path.unlink(missing_ok=True)
    
    def test_invalid_config_values(self):
        """Test configuration validation with invalid values"""
        with pytest.raises(ConfigurationException):
            DatabaseConfig(timeout=-1)
        
        with pytest.raises(ConfigurationException):
            AgentConfig(max_workers=0)
        
        with pytest.raises(ConfigurationException):
            LoggingConfig(level="INVALID")


class TestEnhancedBackendManager:
    """Test enhanced backend manager with circuit breaker"""
    
    @pytest.fixture
    def mock_backend_manager(self):
        """Create mock backend manager for testing"""
        manager = EnhancedLLMBackendManager()
        
        # Mock the backends
        mock_ollama = Mock()
        mock_ollama.is_available.return_value = True
        mock_ollama.chat = AsyncMock(return_value=LLMResponse(
            content="Test response",
            model="test-model",
            backend="ollama"
        ))
        
        mock_zluda = Mock()
        mock_zluda.is_available.return_value = True
        mock_zluda.chat = AsyncMock(return_value=LLMResponse(
            content="ZLUDA response",
            model="test-model", 
            backend="zluda"
        ))
        
        manager.backends = {
            'ollama': mock_ollama,
            'zluda': mock_zluda
        }
        manager.default_backend = 'ollama'
        
        return manager
    
    @pytest.mark.asyncio
    async def test_successful_chat(self, mock_backend_manager):
        """Test successful chat request"""
        response = await mock_backend_manager.chat_with_fallback(
            messages=[{"role": "user", "content": "Hello"}],
            model="test-model"
        )
        
        assert response.content == "Test response"
        assert response.backend == "ollama"
        assert response.response_time > 0
    
    @pytest.mark.asyncio
    async def test_fallback_on_failure(self, mock_backend_manager):
        """Test fallback to secondary backend on primary failure"""
        # Make primary backend fail
        mock_backend_manager.backends['ollama'].chat.side_effect = Exception("Primary failed")
        
        response = await mock_backend_manager.chat_with_fallback(
            messages=[{"role": "user", "content": "Hello"}],
            model="test-model"
        )
        
        assert response.content == "ZLUDA response"
        assert response.backend == "zluda"
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens(self, mock_backend_manager):
        """Test circuit breaker opens after threshold failures"""
        # Set low threshold for testing
        mock_backend_manager.circuit_breaker_threshold = 2
        
        # Make backend fail
        mock_backend_manager.backends['ollama'].chat.side_effect = Exception("Backend error")
        
        # First failure
        with pytest.raises(BackendUnavailableException):
            await mock_backend_manager.chat_with_fallback(
                messages=[{"role": "user", "content": "Hello"}],
                model="test-model"
            )
        
        # Second failure should open circuit breaker
        with pytest.raises(BackendUnavailableException):
            await mock_backend_manager.chat_with_fallback(
                messages=[{"role": "user", "content": "Hello"}],
                model="test-model"
            )
        
        # Check circuit breaker status
        health = mock_backend_manager.backend_health['ollama']
        assert health.status == BackendStatus.CIRCUIT_OPEN
        assert health.metrics.circuit_failures >= 2
    
    def test_health_report(self, mock_backend_manager):
        """Test backend health reporting"""
        # Simulate some metrics
        health = mock_backend_manager.backend_health['ollama']
        health.metrics.total_requests = 10
        health.metrics.successful_requests = 8
        health.metrics.avg_response_time = 1.5
        
        report = mock_backend_manager.get_backend_health_report()
        
        assert 'ollama' in report
        assert report['ollama']['success_rate'] == 0.8
        assert report['ollama']['avg_response_time'] == 1.5
        assert report['ollama']['total_requests'] == 10


class MockAgent:
    """Mock agent for testing mixins"""
    
    def __init__(self, agent_id="test-agent", model="test-model", **kwargs):
        self.agent_id = agent_id
        self.model = model
        # Call super().__init__() for proper mixin initialization
        super().__init__(**kwargs)
        
    async def send_message(self, receiver_id, message_type, content, request_id=None):
        """Mock send_message method"""
        pass


class TestAgentMixins:
    """Test agent mixin functionality"""
    
    def test_task_decomposition_mixin(self):
        """Test task decomposition mixin"""
        
        class TestAgent(MockAgent, TaskDecompositionMixin):
            pass
        
        agent = TestAgent()
        
        # Test prompt building
        prompt = agent._build_decomposition_prompt(
            "Create a web app", 
            "Python Flask", 
            5, 
            "worker"
        )
        
        assert "Create a web app" in prompt
        assert "Python Flask" in prompt
        assert "worker agents" in prompt
        assert "5" in prompt
    
    @pytest.mark.asyncio
    async def test_task_decomposition_parsing(self):
        """Test task decomposition response parsing"""
        
        class TestAgent(MockAgent, TaskDecompositionMixin):
            pass
        
        agent = TestAgent()
        
        # Test valid JSON response
        json_response = '["Task 1", "Task 2", "Task 3"]'
        result = agent._parse_decomposition_response(json_response, "fallback", 10)
        assert result == ["Task 1", "Task 2", "Task 3"]
        
        # Test invalid JSON fallback
        invalid_response = "Not valid JSON"
        result = agent._parse_decomposition_response(invalid_response, "fallback task", 10)
        assert result == ["fallback task"]
        
        # Test line-based fallback
        line_response = """
        1. First task to complete
        2. Second task to complete  
        3. Third task to complete
        """
        result = agent._parse_decomposition_response(line_response, "fallback", 10)
        assert len(result) == 3
        assert "First task to complete" in result[0]
    
    @pytest.mark.asyncio
    async def test_message_handling_mixin(self):
        """Test message handling mixin"""
        
        class TestAgent(MockAgent, MessageHandlingMixin):
            def __init__(self):
                super().__init__()
                self.sent_messages = []
                
            async def send_message(self, receiver_id, message_type, content, request_id=None):
                self.sent_messages.append({
                    'receiver_id': receiver_id,
                    'message_type': message_type,
                    'content': content,
                    'request_id': request_id
                })
        
        agent = TestAgent()
        
        # Mock message object
        mock_message = Mock()
        mock_message.content = "Test error"
        mock_message.sender_id = "test-sender"
        mock_message.request_id = "req-123"
        
        # Test error handling
        await agent.handle_error_message(mock_message)
        
        assert len(agent.sent_messages) == 1
        sent = agent.sent_messages[0]
        assert sent['receiver_id'] == "orchestrator"
        assert sent['message_type'] == "final-error"
        assert "Test error" in sent['content']
        assert sent['request_id'] == "req-123"
    
    def test_performance_tracking_mixin(self):
        """Test performance tracking mixin"""
        
        class TestAgent(MockAgent, PerformanceTrackingMixin):
            pass
        
        agent = TestAgent()
        
        # Check initial metrics
        assert agent.performance_metrics['tasks_processed'] == 0
        assert agent.performance_metrics['tasks_successful'] == 0
        
        # Get initial report
        report = agent.get_performance_report()
        assert report['success_rate'] == 0.0
        assert report['agent_id'] == "test-agent"
    
    def test_validation_mixin(self):
        """Test validation mixin"""
        
        class TestAgent(MockAgent, ValidationMixin):
            pass
        
        agent = TestAgent()
        
        # Test valid task content
        content = agent.validate_task_content("Create a simple function")
        assert content == "Create a simple function"
        
        # Test invalid task content
        with pytest.raises(Exception):  # ValidationException would be imported
            agent.validate_task_content("")
        
        with pytest.raises(Exception):
            agent.validate_task_content("x" * 20000)  # Too long
        
        # Test file path validation
        valid_path = agent.validate_file_path("test.py", ['.py', '.txt'])
        assert valid_path == "test.py"
        
        with pytest.raises(Exception):
            agent.validate_file_path("../../../etc/passwd")  # Path traversal
        
        with pytest.raises(Exception):
            agent.validate_file_path("test.exe", ['.py', '.txt'])  # Invalid extension


class TestIntegration:
    """Integration tests for the refactored system"""
    
    @pytest.mark.asyncio
    async def test_config_backend_integration(self):
        """Test configuration system with backend manager"""
        # Create config with specific backend settings
        config = OllamaFlowConfig()
        config.default_backend = "ollama"
        config.performance.circuit_breaker_threshold = 3
        config.performance.circuit_breaker_timeout = 30
        
        # Create backend manager with config
        manager = EnhancedLLMBackendManager(
            circuit_breaker_threshold=config.performance.circuit_breaker_threshold,
            circuit_breaker_timeout=config.performance.circuit_breaker_timeout
        )
        
        assert manager.circuit_breaker_threshold == 3
        assert manager.circuit_breaker_timeout == 30
    
    def test_exception_configuration_integration(self):
        """Test exceptions work with configuration system"""
        # Test configuration exception
        with pytest.raises(ConfigurationException):
            config = OllamaFlowConfig()
            config.project_root = Path("/nonexistent/path")
            config.__post_init__()
    
    @pytest.mark.asyncio  
    async def test_mixin_backend_integration(self):
        """Test mixins work with backend system"""
        
        class TestAgent(MockAgent, TaskDecompositionMixin):
            pass
        
        agent = TestAgent()
        
        # Mock backend manager
        with patch('agents.mixins.backend_manager') as mock_manager:
            mock_manager.chat_with_fallback = AsyncMock(return_value=LLMResponse(
                content='["Task 1", "Task 2"]',
                model="test-model",
                backend="test-backend"
            ))
            
            result = await agent.decompose_task("Test task")
            assert result == ["Task 1", "Task 2"]
            
            # Verify backend was called correctly
            mock_manager.chat_with_fallback.assert_called_once()
            call_args = mock_manager.chat_with_fallback.call_args
            assert call_args[1]['model'] == 'test-model'
            assert call_args[1]['timeout'] == 30.0


def run_comprehensive_tests():
    """Run all tests and return results"""
    import subprocess
    import sys
    
    print("🧪 Running Comprehensive Refactored System Tests")
    print("=" * 60)
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            __file__, 
            '-v', 
            '--tb=short',
            '--no-header'
        ], capture_output=True, text=True, timeout=120)
        
        print("Test Output:")
        print("-" * 40)
        print(result.stdout)
        
        if result.stderr:
            print("Errors:")
            print("-" * 40)
            print(result.stderr)
        
        print("-" * 40)
        if result.returncode == 0:
            print("✅ All tests passed!")
            return True
        else:
            print("❌ Some tests failed!")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Tests timed out!")
        return False
    except Exception as e:
        print(f"💥 Test execution failed: {e}")
        return False


if __name__ == "__main__":
    # Run as standalone test script
    success = run_comprehensive_tests()
    
    if not success:
        print("\n🔧 Manual Test Execution")
        print("=" * 30)
        
        # Run basic tests manually if pytest fails
        try:
            # Test exceptions
            print("Testing exceptions...")
            test_exc = TestExceptions()
            test_exc.test_base_exception()
            test_exc.test_backend_exception_hierarchy()
            print("✅ Exception tests passed")
            
            # Test configuration
            print("Testing configuration...")
            test_config = TestConfiguration()
            test_config.test_default_config_creation()
            print("✅ Configuration tests passed")
            
            print("\n✅ Basic manual tests completed successfully!")
            
        except Exception as e:
            print(f"❌ Manual tests failed: {e}")
            import traceback
            traceback.print_exc()
    
    sys.exit(0 if success else 1)