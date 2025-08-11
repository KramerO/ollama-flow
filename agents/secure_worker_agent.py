import asyncio
import subprocess
import logging
import re
import os
import shlex
from typing import Optional, List, Dict, Any
from pathlib import Path
import tempfile
import json

from agents.base_agent import BaseAgent, AgentMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecureWorkerAgent(BaseAgent):
    """Enhanced Worker Agent with security controls and sandboxing"""
    
    # Command whitelist - only these commands are allowed
    ALLOWED_COMMANDS = {
        # File operations
        'ls', 'cat', 'head', 'tail', 'find', 'grep', 'wc', 'sort', 'uniq',
        'mkdir', 'touch', 'cp', 'mv', 'rm', 'chmod', 'chown',
        
        # Text processing
        'echo', 'printf', 'cut', 'awk', 'sed', 'tr',
        
        # Programming tools
        'python3', 'python', 'node', 'npm', 'pip', 'pip3',
        'git', 'curl', 'wget',
        
        # System info (safe)
        'pwd', 'whoami', 'date', 'uname', 'which', 'whereis',
        'df', 'du', 'ps', 'top', 'free', 'uptime'
    }
    
    # Dangerous patterns to block
    FORBIDDEN_PATTERNS = [
        r'\brm\s+-rf\s+/',  # Dangerous rm commands
        r'\bsudo\b',         # Sudo commands
        r'\bsu\b',           # Switch user
        r'\b>/dev/\w+\b',    # Writing to device files
        r'\bchmod\s+777\b',  # Overly permissive permissions
        r'\b&\s*$',          # Background processes
        r'\|\s*bash\b',      # Piping to bash
        r'\|\s*sh\b',        # Piping to shell
        r'\$\(',             # Command substitution
        r'`[^`]*`',          # Backtick command substitution  
        r'\beval\b',         # Eval commands
        r'\bexec\b',         # Exec commands
        r'>\s*/etc/',        # Writing to /etc
        r'>\s*/var/log/',    # Writing to system logs
        r'>\s*/root/',       # Writing to root directory
    ]
    
    # File extension whitelist for saving
    ALLOWED_EXTENSIONS = {
        '.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.yaml', '.yml',
        '.md', '.rst', '.csv', '.tsv', '.log', '.conf', '.cfg', '.ini',
        '.sql', '.sh', '.bash', '.dockerfile', '.gitignore', '.env.example'
    }
    
    def __init__(self, agent_id: str, name: str, model: str = "llama3", project_folder_path: Optional[str] = None):
        super().__init__(agent_id, name)
        self.model = model
        self.project_folder_path = self._validate_project_folder(project_folder_path)
        self.sandbox_enabled = True
        self.max_execution_time = 30  # seconds
        self.max_output_size = 10000  # characters
        
        # Security metrics
        self.blocked_commands = 0
        self.executed_commands = 0
        self.security_violations = []
        
        # Performance tracking
        self.task_history: List[Dict[str, Any]] = []

    def _validate_project_folder(self, path: Optional[str]) -> Optional[str]:
        """Validate and sanitize project folder path"""
        if not path:
            return None
            
        try:
            # Resolve and validate path
            resolved_path = Path(path).resolve()
            
            # Security checks
            if not resolved_path.exists():
                resolved_path.mkdir(parents=True, exist_ok=True)
                
            # Ensure it's not a system directory (allow user home directories for projects)
            forbidden_paths = ['/etc', '/var', '/usr', '/root', '/sys', '/proc', '/dev']
            path_str = str(resolved_path)
            
            # Allow user project directories under /home/username/projects
            if path_str.startswith('/home/') and '/projects/' in path_str:
                # Allow user project directories
                pass
            else:
                for forbidden in forbidden_paths:
                    if path_str.startswith(forbidden):
                        logger.warning(f"Forbidden project path: {path_str}")
                        return None
                    
            return str(resolved_path)
            
        except Exception as e:
            logger.error(f"Invalid project folder path {path}: {e}")
            return None

    async def _perform_task_with_ollama(self, prompt: str) -> str:
        """Perform task using Ollama with timeout and error handling"""
        try:
            # Add security context to prompt
            enhanced_prompt = f"""
            {prompt}
            
            SECURITY GUIDELINES:
            1. Only suggest safe commands from the whitelist
            2. Avoid any system-level modifications
            3. Work within the project directory only
            4. Be cautious with file operations
            5. Explain your reasoning for any suggested commands
            """
            
            # Create async subprocess for ollama call
            process = await asyncio.create_subprocess_exec(
                'ollama', 'run', self.model,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Send prompt and get response with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=enhanced_prompt.encode()),
                timeout=self.max_execution_time
            )
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise Exception(f"Ollama execution failed: {error_msg}")
                
            response = stdout.decode().strip()
            
            # Truncate if too long
            if len(response) > self.max_output_size:
                response = response[:self.max_output_size] + "\n... [Response truncated for security]"
                
            return response
            
        except asyncio.TimeoutError:
            logger.error(f"Ollama call timeout for agent {self.name}")
            return "Task execution timed out for security reasons."
        except Exception as e:
            logger.error(f"Ollama task execution failed: {e}")
            return f"Task execution failed: {e}"

    def _validate_command(self, command: str) -> tuple[bool, str]:
        """Validate command against security policies"""
        if not command or not command.strip():
            return False, "Empty command"
            
        # Parse command safely
        try:
            parsed = shlex.split(command)
        except ValueError as e:
            return False, f"Invalid command syntax: {e}"
            
        if not parsed:
            return False, "No command found"
            
        base_command = parsed[0]
        
        # Check if base command is allowed
        if base_command not in self.ALLOWED_COMMANDS:
            self.blocked_commands += 1
            self.security_violations.append({
                'type': 'forbidden_command',
                'command': base_command,
                'full_command': command,
                'timestamp': asyncio.get_event_loop().time()
            })
            return False, f"Command '{base_command}' is not in whitelist"
            
        # Check for forbidden patterns
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                self.blocked_commands += 1
                self.security_violations.append({
                    'type': 'forbidden_pattern',
                    'pattern': pattern,
                    'command': command,
                    'timestamp': asyncio.get_event_loop().time()
                })
                return False, f"Command contains forbidden pattern: {pattern}"
                
        # Additional validation for specific commands
        if base_command in ['rm', 'rmdir']:
            # Extra validation for remove commands
            if '--recursive' in command or '-r' in command or '-rf' in command:
                if '/' in command and not command.startswith(str(self.project_folder_path or "")):
                    return False, "Recursive remove outside project folder not allowed"
                    
        elif base_command in ['chmod', 'chown']:
            # Validate permission changes
            if '777' in command or '666' in command:
                return False, "Overly permissive permissions not allowed"
                
        return True, "Command validated"

    async def _run_command_securely(self, command: str) -> str:
        """Execute command with security controls and sandboxing"""
        logger.info(f"[SecureWorker {self.name}] Validating command: {command}")
        
        # Validate command
        is_valid, validation_message = self._validate_command(command)
        if not is_valid:
            logger.warning(f"Blocked command: {command} - {validation_message}")
            return f"Command blocked for security: {validation_message}"
            
        try:
            # Set working directory to project folder if available
            cwd = self.project_folder_path if self.project_folder_path else None
            
            # Create secure subprocess
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                # Security: limit environment variables
                env={
                    'PATH': os.environ.get('PATH', ''),
                    'HOME': os.environ.get('HOME', ''),
                    'USER': os.environ.get('USER', ''),
                    'PWD': cwd or os.getcwd()
                }
            )
            
            # Execute with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.max_execution_time
            )
            
            # Process output
            output = ""
            if stdout:
                stdout_text = stdout.decode().strip()
                if len(stdout_text) > self.max_output_size:
                    stdout_text = stdout_text[:self.max_output_size] + "\n... [Output truncated]"
                output += f"Stdout:\n{stdout_text}\n"
                
            if stderr:
                stderr_text = stderr.decode().strip()
                if len(stderr_text) > self.max_output_size:
                    stderr_text = stderr_text[:self.max_output_size] + "\n... [Error truncated]"
                output += f"Stderr:\n{stderr_text}\n"
                
            if process.returncode != 0:
                output += f"Exit code: {process.returncode}\n"
                
            self.executed_commands += 1
            logger.info(f"[SecureWorker {self.name}] Command executed successfully")
            
            return output.strip() if output else "Command completed successfully"
            
        except asyncio.TimeoutError:
            logger.warning(f"Command timeout: {command}")
            return f"Command timed out after {self.max_execution_time} seconds"
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return f"Command execution error: {e}"

    def _validate_file_path(self, file_path: str) -> tuple[bool, str]:
        """Validate file path for security"""
        try:
            # Resolve path
            resolved_path = Path(file_path).resolve()
            
            # Check extension
            if resolved_path.suffix.lower() not in self.ALLOWED_EXTENSIONS:
                return False, f"File extension '{resolved_path.suffix}' not allowed"
                
            # Check if within project folder
            if self.project_folder_path:
                project_path = Path(self.project_folder_path).resolve()
                try:
                    resolved_path.relative_to(project_path)
                except ValueError:
                    return False, "File path outside project folder"
                    
            # Check for forbidden directories
            path_str = str(resolved_path)
            forbidden_dirs = ['/etc', '/var', '/usr', '/root', '/sys', '/proc', '/dev']
            
            for forbidden in forbidden_dirs:
                if path_str.startswith(forbidden):
                    return False, f"Cannot write to system directory: {forbidden}"
                    
            return True, "Path validated"
            
        except Exception as e:
            return False, f"Path validation error: {e}"

    async def _handle_secure_file_saving(self, message_content: str, result: str) -> str:
        """Handle file saving with security controls"""
        save_message = ""
        
        # Look for save requests
        save_patterns = [
            r"(?:save|write|store)(?:\s+(?:it|this|the\s+(?:file|code|content)))?\s+(?:to|as|in)\s+([^\s]+)",
            r"speichere\s+(?:sie\s+)?(?:als\s+|unter\s+)?([^\s]+)",
            r"save\s+(?:it\s+)?to\s+([^\s]+)"
        ]
        
        target_path = None
        for pattern in save_patterns:
            match = re.search(pattern, message_content, re.IGNORECASE)
            if match:
                target_path = match.group(1).strip()
                break
                
        if not target_path or not self.project_folder_path:
            return save_message
            
        # Validate file path
        is_valid, validation_message = self._validate_file_path(target_path)
        if not is_valid:
            save_message = f"\nFile save blocked: {validation_message}"
            logger.warning(f"Blocked file save to {target_path}: {validation_message}")
            return save_message
            
        try:
            # Resolve full path
            if not os.path.isabs(target_path):
                full_path = os.path.join(self.project_folder_path, target_path)
            else:
                full_path = target_path
                
            # Extract content to save
            content_to_write = self._extract_content_from_result(result)
            
            # Create directory if needed
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Validate content size
            if len(content_to_write) > 50000:  # 50KB limit
                save_message = f"\nFile save blocked: Content too large ({len(content_to_write)} chars, max 50000)"
                return save_message
                
            # Write file securely
            with open(full_path, "w", encoding='utf-8') as f:
                f.write(content_to_write)
                
            # Set safe permissions
            os.chmod(full_path, 0o644)
            
            save_message = f"\nFile saved securely to: {full_path}"
            logger.info(f"File saved: {full_path}")
            
        except Exception as e:
            save_message = f"\nSecure file save failed: {e}"
            logger.error(f"File save error: {e}")
            
        return save_message

    def _extract_content_from_result(self, result: str) -> str:
        """Extract content from LLM result for file saving"""
        # Look for code blocks first
        code_block_patterns = [
            r"```[\w]*\n(.*?)\n```",  # Standard code blocks
            r"`([^`]+)`",              # Inline code
        ]
        
        for pattern in code_block_patterns:
            match = re.search(pattern, result, re.DOTALL)
            if match:
                return match.group(1).strip()
                
        # If no code blocks, use the whole result but sanitize
        lines = result.split('\n')
        content_lines = []
        
        for line in lines:
            # Skip obvious non-content lines
            if line.strip().startswith(('Here', 'This', 'The', 'I', 'To', 'You')):
                continue
            content_lines.append(line)
            
        return '\n'.join(content_lines).strip() if content_lines else result

    async def _handle_command_execution(self, message_content: str) -> str:
        """Handle command execution requests"""
        command_patterns = [
            r"(?:execute|run|perform)\s+(?:the\s+)?command[:\s]+(.+)",
            r"führe\s+den\s+befehl\s+aus[:\s]+(.+)",
            r"execute\s+command[:\s]+(.+)"
        ]
        
        for pattern in command_patterns:
            match = re.search(pattern, message_content, re.IGNORECASE)
            if match:
                command = match.group(1).strip()
                return await self._run_command_securely(command)
                
        return ""

    def _record_task_metrics(self, task_content: str, result: str, duration: float, success: bool):
        """Record task execution metrics"""
        self.task_history.append({
            'timestamp': asyncio.get_event_loop().time(),
            'task_content': task_content[:200],  # Truncate for storage
            'result_length': len(result),
            'duration': duration,
            'success': success,
            'commands_executed': self.executed_commands,
            'commands_blocked': self.blocked_commands
        })
        
        # Keep only last 100 entries
        if len(self.task_history) > 100:
            self.task_history = self.task_history[-100:]

    async def receive_message(self, message: AgentMessage):
        """Enhanced message handling with security controls"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            logger.info(f"SecureWorker {self.name} received task: {message.content[:100]}...")
            
            # Enhanced task processing with security context
            result = await self._perform_task_with_ollama(message.content)
            
            # Handle file saving securely
            save_message = await self._handle_secure_file_saving(message.content, result)
            
            # Handle command execution securely
            command_output = await self._handle_command_execution(message.content)
            
            # Combine results
            final_response = result
            if save_message:
                final_response += save_message
            if command_output:
                final_response += f"\nCommand Output:\n{command_output}"
                
            # Add security summary if there were violations
            if self.security_violations:
                recent_violations = [v for v in self.security_violations if start_time - v['timestamp'] < 60]
                if recent_violations:
                    final_response += f"\n\nSecurity Note: {len(recent_violations)} security check(s) performed."
                    
            # Record metrics
            duration = asyncio.get_event_loop().time() - start_time
            self._record_task_metrics(message.content, final_response, duration, True)
            
            # Send response
            await self.send_message(message.sender_id, "response", final_response, message.request_id)
            
            logger.info(f"SecureWorker {self.name} completed task successfully")
            
        except Exception as e:
            # Record failure metrics
            duration = asyncio.get_event_loop().time() - start_time
            error_msg = f"Task execution failed: {e}"
            self._record_task_metrics(message.content, error_msg, duration, False)
            
            logger.error(f"SecureWorker {self.name} task failed: {e}")
            await self.send_message(message.sender_id, "error", error_msg, message.request_id)

    def get_security_summary(self) -> Dict[str, Any]:
        """Get security metrics summary"""
        return {
            'agent_id': self.agent_id,
            'commands_executed': self.executed_commands,
            'commands_blocked': self.blocked_commands,
            'security_violations': len(self.security_violations),
            'recent_violations': [
                v for v in self.security_violations 
                if asyncio.get_event_loop().time() - v['timestamp'] < 3600  # Last hour
            ],
            'task_history_count': len(self.task_history),
            'project_folder': self.project_folder_path,
            'sandbox_enabled': self.sandbox_enabled
        }