#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures for Ollama Flow tests
"""

import pytest
import sys
import os
import tempfile
import platform
from pathlib import Path
from unittest.mock import Mock, patch

# Add project paths to Python path
PROJECT_ROOT = Path(__file__).parent.parent
PYTHON_DIR = PROJECT_ROOT / "ollama-flow-python"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PYTHON_DIR))

# Platform detection
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"
IS_MACOS = platform.system() == "Darwin"

# Test configuration
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "windows: mark test as Windows-specific"
    )
    config.addinivalue_line(
        "markers", "linux: mark test as Linux-specific"
    )
    config.addinivalue_line(
        "markers", "macos: mark test as macOS-specific"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle platform-specific tests"""
    skip_windows = pytest.mark.skip(reason="Windows-specific test")
    skip_linux = pytest.mark.skip(reason="Linux-specific test")
    skip_macos = pytest.mark.skip(reason="macOS-specific test")
    
    for item in items:
        # Skip Windows tests on non-Windows platforms
        if "windows" in item.keywords and not IS_WINDOWS:
            item.add_marker(skip_windows)
        
        # Skip Linux tests on non-Linux platforms
        if "linux" in item.keywords and not IS_LINUX:
            item.add_marker(skip_linux)
            
        # Skip macOS tests on non-macOS platforms
        if "macos" in item.keywords and not IS_MACOS:
            item.add_marker(skip_macos)

@pytest.fixture(scope="session")
def project_root():
    """Project root directory fixture"""
    return PROJECT_ROOT

@pytest.fixture(scope="session")
def python_dir():
    """Python framework directory fixture"""
    return PYTHON_DIR

@pytest.fixture
def temp_dir():
    """Temporary directory fixture"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def temp_db():
    """Temporary SQLite database fixture"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
        db_path = temp_file.name
    yield db_path
    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass

@pytest.fixture
def mock_ollama():
    """Mock Ollama client for testing"""
    with patch('ollama.chat') as mock_chat, \
         patch('ollama.list') as mock_list, \
         patch('ollama.pull') as mock_pull:
        
        # Configure mock responses
        mock_chat.return_value = {
            'message': {'content': 'Mocked Ollama response'}
        }
        mock_list.return_value = {
            'models': [
                {'name': 'codellama:7b', 'size': 3800000000},
                {'name': 'llama3', 'size': 4700000000}
            ]
        }
        mock_pull.return_value = True
        
        yield {
            'chat': mock_chat,
            'list': mock_list,
            'pull': mock_pull
        }

@pytest.fixture
def mock_psutil():
    """Mock psutil for system monitoring tests"""
    with patch('psutil.cpu_percent', return_value=45.0), \
         patch('psutil.virtual_memory') as mock_mem, \
         patch('psutil.disk_usage') as mock_disk, \
         patch('psutil.pids', return_value=list(range(100))):
        
        mock_mem.return_value.percent = 65.0
        mock_disk.return_value.percent = 30.0
        
        yield {
            'cpu_percent': 45.0,
            'memory_percent': 65.0,
            'disk_percent': 30.0
        }

@pytest.fixture
def mock_flask_app():
    """Mock Flask application for dashboard tests"""
    try:
        from flask import Flask
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        return app
    except ImportError:
        pytest.skip("Flask not available")

@pytest.fixture
def mock_subprocess():
    """Mock subprocess for CLI tests"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Mocked command output",
            stderr=""
        )
        yield mock_run

@pytest.fixture
def sample_session_data():
    """Sample session data for testing"""
    return {
        'id': 'test_session_123',
        'name': 'Test Session',
        'task': 'Sample test task for unit testing',
        'workers': 4,
        'architecture': 'HIERARCHICAL',
        'model': 'codellama:7b',
        'status': 'running',
        'started_at': '2024-01-01T10:00:00Z',
        'project_folder': '/tmp/test_project'
    }

@pytest.fixture
def sample_neural_pattern():
    """Sample neural intelligence pattern for testing"""
    return {
        'pattern_type': 'task_decomposition',
        'input_data': {
            'task': 'Build a web application',
            'workers': 6,
            'architecture': 'HIERARCHICAL'
        },
        'output_data': {
            'success': True,
            'execution_time': 45.2,
            'subtasks_created': 8,
            'completion_rate': 0.95
        },
        'confidence': 0.87,
        'learned_at': '2024-01-01T10:00:00Z'
    }

@pytest.fixture
def sample_monitoring_data():
    """Sample monitoring data for testing"""
    return {
        'timestamp': '2024-01-01T10:00:00Z',
        'cpu_percent': 45.0,
        'memory_percent': 65.0,
        'disk_percent': 30.0,
        'active_sessions': 2,
        'completed_tasks': 15,
        'system_health_score': 87.5
    }

@pytest.fixture
def cli_wrapper_content():
    """CLI wrapper content for testing"""
    wrapper_path = PROJECT_ROOT / "ollama-flow.bat"
    if wrapper_path.exists():
        return wrapper_path.read_text(encoding='utf-8', errors='ignore')
    return ""

@pytest.fixture
def install_script_content():
    """Installation script content for testing"""
    install_path = PROJECT_ROOT / "install_windows.bat"
    if install_path.exists():
        return install_path.read_text(encoding='utf-8', errors='ignore')
    return ""

@pytest.fixture
def requirements_content():
    """Requirements.txt content for testing"""
    req_path = PYTHON_DIR / "requirements.txt"
    if req_path.exists():
        return req_path.read_text()
    return ""

# Utility functions for tests
def create_mock_project_structure(base_dir):
    """Create a mock project structure for testing"""
    base_path = Path(base_dir)
    
    # Create directory structure
    dirs = [
        "ollama-flow-python",
        "ollama-flow-python/agents", 
        "ollama-flow-python/dashboard",
        "ollama-flow-python/tests",
        "src",
        "dashboard"
    ]
    
    for dir_name in dirs:
        (base_path / dir_name).mkdir(parents=True, exist_ok=True)
    
    # Create essential files
    files = {
        "package.json": '{"name": "ollama-flow", "version": "1.0.0"}',
        "ollama-flow-python/enhanced_main.py": "# Enhanced main file",
        "ollama-flow-python/requirements.txt": "ollama\nflask\npsutil",
        "ollama-flow.bat": "@echo off\necho CLI Wrapper",
        "README.md": "# Ollama Flow"
    }
    
    for file_path, content in files.items():
        full_path = base_path / file_path
        full_path.write_text(content)
    
    return base_path

# Test skip conditions
def skip_if_no_ollama():
    """Skip test if Ollama is not available"""
    try:
        import subprocess
        result = subprocess.run(['ollama', '--version'], 
                              capture_output=True, timeout=5)
        if result.returncode != 0:
            return pytest.mark.skip(reason="Ollama not available")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return pytest.mark.skip(reason="Ollama not available")
    return lambda func: func

def skip_if_no_node():
    """Skip test if Node.js is not available"""
    try:
        import subprocess
        result = subprocess.run(['node', '--version'], 
                              capture_output=True, timeout=5)
        if result.returncode != 0:
            return pytest.mark.skip(reason="Node.js not available")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return pytest.mark.skip(reason="Node.js not available")
    return lambda func: func

def skip_if_no_python_venv():
    """Skip test if Python venv is not available"""
    try:
        import venv
        return lambda func: func
    except ImportError:
        return pytest.mark.skip(reason="Python venv not available")

# Custom pytest markers for categorizing tests
pytestmark = [
    pytest.mark.filterwarnings("ignore::DeprecationWarning"),
    pytest.mark.filterwarnings("ignore::PendingDeprecationWarning"),
]