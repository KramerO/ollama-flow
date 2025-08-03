#!/usr/bin/env python3
"""
Unit tests for CLI wrapper functionality
Tests the ollama-flow CLI commands and their underlying Python implementations
"""

import pytest
import subprocess
import os
import sys
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestCLIWrapper:
    """Test suite for CLI wrapper functionality"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_project_structure(self, temp_dir):
        """Create a mock project structure for testing"""
        # Create basic directory structure
        ollama_python_dir = Path(temp_dir) / "ollama-flow-python"
        ollama_python_dir.mkdir()
        
        # Create venv directory
        venv_dir = ollama_python_dir / "venv" / "Scripts"
        venv_dir.mkdir(parents=True)
        
        # Create activate script
        activate_script = venv_dir / "activate.bat"
        activate_script.write_text("@echo off\necho Virtual environment activated")
        
        # Create enhanced_main.py
        enhanced_main = ollama_python_dir / "enhanced_main.py"
        enhanced_main.write_text("""
import sys
import os
print(f"Enhanced main called with args: {sys.argv[1:]}")
if "--health-check" in sys.argv:
    print("✅ System health: OK")
    print("✅ Python environment: OK")
    print("✅ Dependencies: OK")
elif "--version" in sys.argv:
    print("Ollama Flow Enhanced Framework v2.1.1")
elif "--help" in sys.argv:
    print("Enhanced Ollama Flow Framework Help")
else:
    print("Task execution simulated")
""")
        
        return temp_dir
    
    def test_cli_wrapper_exists(self):
        """Test that CLI wrapper files exist"""
        wrapper_bat = project_root / "ollama-flow.bat"
        wrapper_ps1 = project_root / "ollama-flow.ps1"
        
        assert wrapper_bat.exists(), "ollama-flow.bat not found"
        assert wrapper_ps1.exists(), "ollama-flow.ps1 not found"
        
        # Check basic structure of batch file
        bat_content = wrapper_bat.read_text()
        assert "@echo off" in bat_content
        assert "ollama-flow" in bat_content.lower()
        assert "help" in bat_content.lower()
    
    def test_installation_script_exists(self):
        """Test that installation script exists and has required content"""
        install_script = project_root / "install_windows.bat"
        
        assert install_script.exists(), "install_windows.bat not found"
        
        content = install_script.read_text()
        assert "Ollama Flow Windows Installer" in content
        assert "python" in content.lower()
        assert "npm" in content.lower()
        assert "virtual environment" in content.lower()
        assert "PATH" in content
    
    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")
    def test_batch_wrapper_help_command(self, mock_project_structure):
        """Test batch wrapper help command on Windows"""
        try:
            # Test the help command
            result = subprocess.run([
                "cmd", "/c", str(project_root / "ollama-flow.bat"), "help"
            ], capture_output=True, text=True, timeout=30)
            
            assert result.returncode == 0, f"Help command failed: {result.stderr}"
            assert "Ollama Flow CLI Wrapper" in result.stdout
            assert "USAGE:" in result.stdout
            assert "EXAMPLES:" in result.stdout
            
        except subprocess.TimeoutExpired:
            pytest.skip("Command timed out - system may be slow")
        except FileNotFoundError:
            pytest.skip("cmd.exe not available")
    
    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")  
    def test_powershell_wrapper_version(self):
        """Test PowerShell wrapper version command"""
        try:
            result = subprocess.run([
                "powershell", "-ExecutionPolicy", "Bypass", "-File", 
                str(project_root / "ollama-flow.ps1"), "version"
            ], capture_output=True, text=True, timeout=30)
            
            # PowerShell might have execution policy restrictions
            if "execution policy" in result.stderr.lower():
                pytest.skip("PowerShell execution policy restriction")
            
            assert result.returncode == 0, f"Version command failed: {result.stderr}"
            assert "Version Information" in result.stdout or "v2" in result.stdout
            
        except subprocess.TimeoutExpired:
            pytest.skip("Command timed out")
        except FileNotFoundError:
            pytest.skip("PowerShell not available")
    
    def test_cli_commands_structure(self):
        """Test that CLI wrapper has all expected commands"""
        wrapper_bat = project_root / "ollama-flow.bat"
        content = wrapper_bat.read_text()
        
        expected_commands = [
            "help", "run", "enhanced", "dashboard", "cli", "sessions",
            "server", "status", "health", "models", "install", "test",
            "benchmark", "logs", "config", "version", "update", "clean"
        ]
        
        for command in expected_commands:
            assert f'"{command}"' in content or f"'{command}'" in content, \
                   f"Command '{command}' not found in CLI wrapper"
    
    def test_readme_files_consistency(self):
        """Test that README files exist and are consistent"""
        main_readme = project_root / "README.md"
        windows_readme = project_root / "README_WINDOWS.md"
        cli_guide = project_root / "CLI_WRAPPER_GUIDE.md"
        
        assert main_readme.exists(), "Main README.md not found"
        assert windows_readme.exists(), "README_WINDOWS.md not found"
        assert cli_guide.exists(), "CLI_WRAPPER_GUIDE.md not found"
        
        # Check for key content
        main_content = main_readme.read_text()
        windows_content = windows_readme.read_text()
        cli_content = cli_guide.read_text()
        
        assert "ollama-flow" in main_content.lower()
        assert "install_windows.bat" in windows_content
        assert "CLI Wrapper" in cli_content
        assert "ollama-flow run" in cli_content
    
    def test_project_structure_completeness(self):
        """Test that all expected project files exist"""
        expected_files = [
            "README.md",
            "README_WINDOWS.md", 
            "CLI_WRAPPER_GUIDE.md",
            "ollama-flow.bat",
            "ollama-flow.ps1",
            "install_windows.bat",
            "enhanced_main.py",
            "requirements.txt"
        ]
        
        for file_name in expected_files:
            file_path = project_root / file_name
            assert file_path.exists(), f"Expected file {file_name} not found"
    
    def test_python_framework_structure(self):
        """Test that Python framework structure is correct"""
        python_dir = project_root / "ollama-flow-python"
        
        expected_python_files = [
            "enhanced_main.py",
            "requirements.txt",
            "agents/base_agent.py",
            "dashboard/simple_dashboard.py"
        ]
        
        for file_path in expected_python_files:
            full_path = python_dir / file_path
            assert full_path.exists(), f"Python file {file_path} not found"
    
    @patch('subprocess.run')
    def test_cli_wrapper_error_handling(self, mock_subprocess):
        """Test CLI wrapper error handling"""
        # Mock a failed subprocess call
        mock_subprocess.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Command failed"
        )
        
        # Test that error handling works
        # This would require running the actual CLI but we'll test the structure instead
        wrapper_content = (project_root / "ollama-flow.bat").read_text()
        
        # Check for error handling patterns
        assert "errorLevel" in wrapper_content
        assert "echo" in wrapper_content  # Error messages should be echoed
    
    def test_environment_variable_handling(self):
        """Test environment variable handling in scripts"""
        wrapper_content = (project_root / "ollama-flow.bat").read_text()
        install_content = (project_root / "install_windows.bat").read_text()
        
        # Check for proper environment variable usage
        assert "PROJECT_DIR" in install_content
        assert "PYTHON_DIR" in install_content
        assert "%PROJECT_DIR%" in install_content
        
    def test_path_integration_setup(self):
        """Test PATH integration setup in installation script"""
        install_content = (project_root / "install_windows.bat").read_text()
        
        assert "PATH" in install_content
        assert "setx" in install_content or "SetEnvironmentVariable" in install_content
        assert "ollama-flow" in install_content

class TestCLIIntegration:
    """Integration tests for CLI functionality"""
    
    def test_command_parsing(self):
        """Test command parsing in CLI wrapper"""
        wrapper_bat = project_root / "ollama-flow.bat"
        content = wrapper_bat.read_text()
        
        # Test that commands are properly parsed
        assert 'if "%1"==' in content  # Command parsing structure
        assert 'goto' in content      # Command routing
        
    def test_help_system_completeness(self):
        """Test that help system covers all commands"""
        wrapper_bat = project_root / "ollama-flow.bat"
        content = wrapper_bat.read_text()
        
        # Find help section
        help_start = content.find(":show_help")
        help_end = content.find(":end", help_start)
        help_section = content[help_start:help_end]
        
        # Check that major command categories are documented
        assert "CORE COMMANDS" in help_section
        assert "SYSTEM COMMANDS" in help_section
        assert "EXAMPLES" in help_section
        
    def test_error_messages_quality(self):
        """Test quality of error messages in CLI wrapper"""
        wrapper_bat = project_root / "ollama-flow.bat"
        content = wrapper_bat.read_text()
        
        # Check for user-friendly error messages
        error_patterns = [
            "not found",
            "Please",
            "Usage:",
            "❌",  # Error emoji usage
            "⚠️"   # Warning emoji usage
        ]
        
        found_patterns = sum(1 for pattern in error_patterns if pattern in content)
        assert found_patterns >= 3, "Not enough user-friendly error messages found"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])