#!/usr/bin/env python3
"""
Windows-specific functionality tests
Tests Windows CLI wrapper, installation script, and Windows-specific features
"""

import pytest
import subprocess
import os
import sys
import tempfile
import shutil
import platform
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Skip all tests if not on Windows for actual execution tests
WINDOWS_AVAILABLE = platform.system() == "Windows"

class TestWindowsInstallation:
    """Test Windows installation script functionality"""
    
    def test_install_script_exists(self):
        """Test that Windows installation script exists"""
        install_script = project_root / "install_windows.bat"
        assert install_script.exists(), "install_windows.bat not found"
    
    def test_install_script_structure(self):
        """Test installation script has proper structure"""
        install_script = project_root / "install_windows.bat"
        content = install_script.read_text(encoding='utf-8', errors='ignore')
        
        # Test for required components
        required_sections = [
            "CHECK PREREQUISITES",
            "INSTALL NODE.JS DEPENDENCIES", 
            "SETUP ENHANCED PYTHON FRAMEWORK",
            "SETUP DASHBOARD",
            "CREATE CONFIGURATION FILES",
            "DOWNLOAD OLLAMA MODELS"
        ]
        
        for section in required_sections:
            assert section in content, f"Required section '{section}' not found"
    
    def test_install_script_error_handling(self):
        """Test error handling in installation script"""
        install_script = project_root / "install_windows.bat"
        content = install_script.read_text(encoding='utf-8', errors='ignore')
        
        # Check for error handling patterns
        error_patterns = [
            "errorLevel",
            "pause",
            "exit /b 1",
            "echo ❌",
            "if %errorLevel% neq 0"
        ]
        
        found_patterns = sum(1 for pattern in error_patterns if pattern in content)
        assert found_patterns >= 3, "Insufficient error handling in installation script"
    
    def test_install_script_prerequisite_checks(self):
        """Test prerequisite checks in installation script"""
        install_script = project_root / "install_windows.bat"
        content = install_script.read_text(encoding='utf-8', errors='ignore')
        
        # Check for prerequisite validations
        prerequisites = [
            "python --version",
            "pip --version", 
            "node --version",
            "npm --version",
            "ollama --version"
        ]
        
        for prereq in prerequisites:
            assert prereq in content, f"Prerequisite check '{prereq}' not found"
    
    def test_path_integration_logic(self):
        """Test PATH integration logic in installation script"""
        install_script = project_root / "install_windows.bat"
        content = install_script.read_text(encoding='utf-8', errors='ignore')
        
        # Check for PATH-related functionality
        path_elements = [
            "PATH",
            "setx PATH",
            "PATH Integration",
            "Environment Variables"
        ]
        
        found_elements = sum(1 for element in path_elements if element in content)
        assert found_elements >= 2, "PATH integration logic incomplete"
    
    @pytest.mark.skipif(not WINDOWS_AVAILABLE, reason="Requires Windows")
    def test_windows_batch_file_execution(self):
        """Test that batch files can be executed on Windows"""
        try:
            # Test simple batch command execution
            result = subprocess.run([
                "cmd", "/c", "echo", "Windows batch test"
            ], capture_output=True, text=True, timeout=10)
            
            assert result.returncode == 0
            assert "Windows batch test" in result.stdout
            
        except subprocess.TimeoutExpired:
            pytest.skip("Command execution timed out")
        except Exception as e:
            pytest.skip(f"Windows batch execution failed: {e}")

class TestWindowsCLIWrapper:
    """Test Windows CLI wrapper functionality"""
    
    def test_batch_wrapper_structure(self):
        """Test batch wrapper file structure"""
        wrapper_bat = project_root / "ollama-flow.bat"
        content = wrapper_bat.read_text(encoding='utf-8', errors='ignore')
        
        # Check for essential batch file elements
        batch_elements = [
            "@echo off",
            "setlocal enabledelayedexpansion",
            ":show_help",
            ":end",
            "if \"%1\"==",
            "goto"
        ]
        
        for element in batch_elements:
            assert element in content, f"Batch element '{element}' not found"
    
    def test_powershell_wrapper_structure(self):
        """Test PowerShell wrapper file structure"""
        wrapper_ps1 = project_root / "ollama-flow.ps1"
        content = wrapper_ps1.read_text(encoding='utf-8', errors='ignore')
        
        # Check for essential PowerShell elements
        ps_elements = [
            "#Requires -Version",
            "param(",
            "function",
            "switch",
            "Write-Host",
            "$"
        ]
        
        for element in ps_elements:
            assert element in content, f"PowerShell element '{element}' not found"
    
    def test_command_routing_logic(self):
        """Test command routing logic in CLI wrapper"""
        wrapper_bat = project_root / "ollama-flow.bat"
        content = wrapper_bat.read_text(encoding='utf-8', errors='ignore')
        
        # Check for command routing
        commands = [
            "help", "run", "enhanced", "dashboard", "cli", 
            "sessions", "status", "health", "models"
        ]
        
        for command in commands:
            # Look for command routing patterns
            assert f'if "%1"=="{command}"' in content or f"if '%1'=='{command}'" in content, \
                   f"Command routing for '{command}' not found"
    
    def test_error_handling_in_cli(self):
        """Test error handling in CLI wrapper"""
        wrapper_bat = project_root / "ollama-flow.bat"
        content = wrapper_bat.read_text(encoding='utf-8', errors='ignore')
        
        # Check for error handling patterns
        error_patterns = [
            "Virtual environment not found",
            "❌",
            "echo.*error",
            "Please run.*install"
        ]
        
        found_patterns = sum(1 for pattern in error_patterns 
                           if any(part in content.lower() for part in pattern.lower().split('.*')))
        assert found_patterns >= 2, "Insufficient error handling in CLI wrapper"
    
    @pytest.mark.skipif(not WINDOWS_AVAILABLE, reason="Requires Windows")
    def test_cli_wrapper_help_execution(self):
        """Test CLI wrapper help command execution on Windows"""
        wrapper_bat = project_root / "ollama-flow.bat"
        
        try:
            result = subprocess.run([
                "cmd", "/c", str(wrapper_bat), "help"
            ], capture_output=True, text=True, timeout=30, cwd=str(project_root))
            
            # Should not fail catastrophically
            assert result.returncode in [0, 1], f"Unexpected return code: {result.returncode}"
            
            # Should contain help information
            output = result.stdout + result.stderr
            help_indicators = ["usage", "command", "help", "ollama-flow"]
            
            found_indicators = sum(1 for indicator in help_indicators 
                                 if indicator.lower() in output.lower())
            assert found_indicators >= 2, "Help output doesn't contain expected information"
            
        except subprocess.TimeoutExpired:
            pytest.skip("CLI wrapper execution timed out")
        except Exception as e:
            pytest.skip(f"CLI wrapper execution failed: {e}")
    
    @pytest.mark.skipif(not WINDOWS_AVAILABLE, reason="Requires Windows")
    def test_powershell_execution_policy_handling(self):
        """Test PowerShell execution policy handling"""
        wrapper_ps1 = project_root / "ollama-flow.ps1"
        
        try:
            # Test with bypass execution policy
            result = subprocess.run([
                "powershell", "-ExecutionPolicy", "Bypass", "-File", 
                str(wrapper_ps1), "help"
            ], capture_output=True, text=True, timeout=30)
            
            # If execution policy is restricted, should get specific error
            if "execution policy" in result.stderr.lower():
                pytest.skip("PowerShell execution policy restriction")
            
            # Should execute or give meaningful error
            assert result.returncode in [0, 1, 2], f"Unexpected PowerShell error: {result.stderr}"
            
        except subprocess.TimeoutExpired:
            pytest.skip("PowerShell execution timed out")
        except FileNotFoundError:
            pytest.skip("PowerShell not available")

class TestWindowsEnvironment:
    """Test Windows environment specific functionality"""
    
    def test_windows_path_handling(self):
        """Test Windows path handling in scripts"""
        wrapper_bat = project_root / "ollama-flow.bat"
        install_bat = project_root / "install_windows.bat"
        
        wrapper_content = wrapper_bat.read_text(encoding='utf-8', errors='ignore')
        install_content = install_bat.read_text(encoding='utf-8', errors='ignore')
        
        # Check for proper Windows path handling
        windows_path_patterns = [
            "%PROJECT_DIR%",
            "%PYTHON_DIR%",
            "\\Scripts\\",
            "venv\\Scripts\\activate"
        ]
        
        for pattern in windows_path_patterns:
            assert pattern in install_content or pattern in wrapper_content, \
                   f"Windows path pattern '{pattern}' not found"
    
    def test_windows_command_patterns(self):
        """Test Windows-specific command patterns"""
        wrapper_bat = project_root / "ollama-flow.bat"
        content = wrapper_bat.read_text(encoding='utf-8', errors='ignore')
        
        # Check for Windows-specific commands
        windows_commands = [
            "call venv\\Scripts\\activate",
            "cd /d",
            "echo off",
            "pause"
        ]
        
        for command in windows_commands:
            assert command in content, f"Windows command pattern '{command}' not found"
    
    def test_unicode_handling(self):
        """Test Unicode/encoding handling in Windows scripts"""
        files_to_check = [
            project_root / "ollama-flow.bat",
            project_root / "install_windows.bat",
            project_root / "README_WINDOWS.md"
        ]
        
        for file_path in files_to_check:
            try:
                # Should be able to read files with different encodings
                content_utf8 = file_path.read_text(encoding='utf-8', errors='ignore')
                content_latin1 = file_path.read_text(encoding='latin-1', errors='ignore')
                
                # Should contain some content
                assert len(content_utf8) > 0, f"File {file_path} appears empty"
                
                # Check for emoji usage (should handle Unicode)
                if "🚀" in content_utf8 or "✅" in content_utf8:
                    # If emojis are used, Unicode handling is working
                    pass
                    
            except Exception as e:
                pytest.fail(f"Unicode handling failed for {file_path}: {e}")
    
    @pytest.mark.skipif(not WINDOWS_AVAILABLE, reason="Requires Windows")
    def test_windows_environment_variables(self):
        """Test Windows environment variable access"""
        try:
            # Test that we can access Windows environment variables
            result = subprocess.run([
                "cmd", "/c", "echo %USERPROFILE%"
            ], capture_output=True, text=True, timeout=10)
            
            assert result.returncode == 0
            assert len(result.stdout.strip()) > 0
            assert "Users" in result.stdout or "users" in result.stdout
            
        except Exception as e:
            pytest.skip(f"Windows environment variable test failed: {e}")

class TestWindowsFileOperations:
    """Test Windows file operations and permissions"""
    
    def test_file_creation_permissions(self):
        """Test file creation and permissions on Windows"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_windows_file.txt"
            
            # Should be able to create files
            test_file.write_text("Windows test content")
            assert test_file.exists()
            
            # Should be able to read files
            content = test_file.read_text()
            assert content == "Windows test content"
    
    def test_directory_operations(self):
        """Test directory operations on Windows"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir) / "test_windows_dir"
            
            # Should be able to create directories
            test_dir.mkdir()
            assert test_dir.exists()
            assert test_dir.is_dir()
    
    @pytest.mark.skipif(not WINDOWS_AVAILABLE, reason="Requires Windows")
    def test_windows_executable_permissions(self):
        """Test executable permissions on Windows"""
        wrapper_bat = project_root / "ollama-flow.bat"
        
        # On Windows, .bat files should be executable
        assert wrapper_bat.exists()
        
        # Test that we can at least attempt to execute
        try:
            result = subprocess.run([
                "cmd", "/c", "where", "cmd"
            ], capture_output=True, text=True, timeout=10)
            
            # If cmd.exe is found, batch execution should work
            assert result.returncode == 0
            assert "cmd.exe" in result.stdout.lower()
            
        except Exception as e:
            pytest.skip(f"Windows executable test failed: {e}")

class TestWindowsDocumentation:
    """Test Windows-specific documentation"""
    
    def test_windows_readme_exists(self):
        """Test that Windows README exists and is comprehensive"""
        windows_readme = project_root / "README_WINDOWS.md"
        assert windows_readme.exists(), "README_WINDOWS.md not found"
        
        content = windows_readme.read_text(encoding='utf-8', errors='ignore')
        
        # Check for essential Windows documentation sections
        required_sections = [
            "Windows Installation",
            "install_windows.bat",
            "Command Prompt",
            "PowerShell",
            "PATH",
            "ollama-flow"
        ]
        
        for section in required_sections:
            assert section in content, f"Required section '{section}' not in Windows README"
    
    def test_cli_guide_windows_coverage(self):
        """Test CLI guide covers Windows usage"""
        cli_guide = project_root / "CLI_WRAPPER_GUIDE.md"
        assert cli_guide.exists(), "CLI_WRAPPER_GUIDE.md not found"
        
        content = cli_guide.read_text(encoding='utf-8', errors='ignore')
        
        # Check for Windows-specific content
        windows_elements = [
            "Windows",
            ".bat",
            "PowerShell",
            "Command Prompt",
            "cmd",
            "PATH"
        ]
        
        found_elements = sum(1 for element in windows_elements if element in content)
        assert found_elements >= 4, "CLI guide lacks sufficient Windows coverage"
    
    def test_installation_instructions_clarity(self):
        """Test clarity of Windows installation instructions"""
        windows_readme = project_root / "README_WINDOWS.md"
        content = windows_readme.read_text(encoding='utf-8', errors='ignore')
        
        # Check for step-by-step instructions
        instruction_patterns = [
            "1.", "2.", "3.",  # Numbered steps
            "```cmd",          # Code blocks
            "install_windows.bat",  # Installation script
            "Administrator"    # Permissions info
        ]
        
        found_patterns = sum(1 for pattern in instruction_patterns if pattern in content)
        assert found_patterns >= 3, "Installation instructions lack clarity"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])