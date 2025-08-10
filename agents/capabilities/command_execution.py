#!/usr/bin/env python3
"""
Command Execution Capability
Handles secure command extraction and execution from LLM responses
"""

import asyncio
import re
import subprocess
import shlex
import os
import time
from typing import List, Dict, Any, Optional, Tuple
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class CommandResult:
    """Result of command execution"""
    command: str
    success: bool
    stdout: str
    stderr: str
    returncode: int
    execution_time: float
    security_check: str

@dataclass
class CommandAnalysis:
    """Analysis of command safety and purpose"""
    is_safe: bool
    risk_level: str  # low, medium, high
    purpose: str
    warnings: List[str]
    suggestions: List[str]

class CommandExecutionCapability:
    """Secure command execution with safety checks and monitoring"""
    
    def __init__(self, agent, settings):
        self.agent = agent
        self.settings = settings
        
        # Command security configuration
        self.allowed_commands = set(settings.security.allowed_commands)
        self.max_timeout = settings.security.max_command_timeout
        self.enable_whitelist = settings.security.enable_command_whitelist
        
        # High-risk commands that require special handling
        self.high_risk_commands = {
            'sudo', 'su', 'rm', 'rmdir', 'mv', 'cp', 'chmod', 'chown',
            'kill', 'killall', 'pkill', 'service', 'systemctl',
            'wget', 'curl', 'ssh', 'scp', 'rsync', 'dd'
        }
        
        # Completely forbidden commands
        self.forbidden_commands = {
            'format', 'fdisk', 'mkfs', 'shutdown', 'reboot', 'halt',
            'rm -rf /', 'rm -rf *', ':(){:|:&};:', '> /dev/sda'
        }
        
        # Command patterns to extract from text
        self.command_patterns = [
            r'```bash\n(.*?)\n```',
            r'```shell\n(.*?)\n```',
            r'```sh\n(.*?)\n```',
            r'```console\n(.*?)\n```',
            r'```terminal\n(.*?)\n```',
            r'```\n(.*?)\n```',  # Generic code blocks (check for commands)
            r'\$\s+(.*?)(?:\n|$)',  # Shell prompts
            r'>\s+(.*?)(?:\n|$)',   # Command prompts
        ]
        
        # Track execution history
        self.execution_history: List[CommandResult] = []
        self.max_history = 100
        
        logger.info(f"✅ Command execution capability initialized with {len(self.allowed_commands)} allowed commands")
    
    async def configure_for_role(self, role, is_priority: bool):
        """Configure command execution based on agent role"""
        role_command_sets = {
            'developer': [
                'git', 'python', 'pip', 'npm', 'node', 'yarn', 'docker', 'docker-compose',
                'ls', 'cat', 'grep', 'find', 'mkdir', 'touch', 'cp', 'mv', 'which', 'whereis'
            ],
            'security_specialist': [
                'nmap', 'netstat', 'ss', 'lsof', 'ps', 'top', 'htop', 'iptables',
                'openssl', 'gpg', 'ssh-keygen', 'chmod', 'chown', 'ls', 'cat', 'grep'
            ],
            'datascientist': [
                'python', 'jupyter', 'pip', 'conda', 'R', 'Rscript',
                'ls', 'cat', 'head', 'tail', 'grep', 'awk', 'sed', 'sort', 'uniq'
            ],
            'it_architect': [
                'docker', 'kubectl', 'terraform', 'ansible', 'systemctl', 'service',
                'ps', 'netstat', 'df', 'du', 'free', 'uname', 'lscpu', 'lsmem'
            ],
            'analyst': [
                'ls', 'cat', 'grep', 'find', 'wc', 'sort', 'uniq', 'head', 'tail',
                'awk', 'sed', 'cut', 'tr', 'date', 'cal'
            ]
        }
        
        role_commands = role_command_sets.get(role.value, [])
        if is_priority and role_commands:
            # Add role-specific commands to allowed list
            self.allowed_commands.update(role_commands)
            logger.info(f"🎯 Added {len(role_commands)} role-specific commands for {role.value}")
    
    async def should_execute(self, task: str, llm_response: str) -> bool:
        """Determine if command execution should be applied"""
        if not self.settings.agents.enable_command_execution:
            return False
        
        # Check for command execution indicators
        execution_indicators = [
            'run', 'execute', 'command', 'terminal', 'bash', 'shell', 'script',
            'install', 'setup', 'configure', 'check', 'test', 'build'
        ]
        
        task_lower = task.lower()
        has_execution_request = any(indicator in task_lower for indicator in execution_indicators)
        
        # Check if response contains command blocks
        has_command_blocks = any(
            re.search(pattern, llm_response, re.MULTILINE | re.DOTALL)
            for pattern in self.command_patterns
        )
        
        return has_execution_request or has_command_blocks
    
    async def execute(self, task: str, llm_response: str) -> str:
        """Extract and execute commands from LLM response"""
        try:
            # Extract all potential commands
            commands = self._extract_commands(llm_response)
            
            if not commands:
                logger.info("ℹ️ No executable commands found in response")
                return llm_response
            
            logger.info(f"🔍 Found {len(commands)} potential commands to execute")
            
            execution_results = []
            
            for i, command in enumerate(commands):
                logger.info(f"🔍 Analyzing command {i+1}/{len(commands)}: {command[:50]}...")
                
                # Analyze command safety
                analysis = await self._analyze_command_safety(command)
                
                if analysis.is_safe:
                    # Execute the command
                    result = await self._execute_command_safely(command, analysis)
                    execution_results.append(result)
                else:
                    # Log rejection
                    logger.warning(f"⚠️ Command rejected: {command} (Risk: {analysis.risk_level})")
                    execution_results.append(CommandResult(
                        command=command,
                        success=False,
                        stdout="",
                        stderr=f"Command rejected: {', '.join(analysis.warnings)}",
                        returncode=-1,
                        execution_time=0.0,
                        security_check=analysis.risk_level
                    ))
            
            # Generate execution summary
            enhanced_response = llm_response + self._generate_execution_summary(execution_results)
            
            return enhanced_response
            
        except Exception as e:
            logger.error(f"❌ Command execution failed: {e}")
            return llm_response + f"\n\n⚠️ Command execution error: {str(e)}"
    
    def _extract_commands(self, text: str) -> List[str]:
        """Extract executable commands from text"""
        commands = []
        
        for pattern in self.command_patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
            for match in matches:
                # Split multi-line command blocks
                command_lines = [line.strip() for line in match.split('\n') if line.strip()]
                
                for line in command_lines:
                    # Skip comments and empty lines
                    if line.startswith('#') or not line:
                        continue
                    
                    # Clean up command
                    clean_command = self._clean_command(line)
                    if clean_command and self._looks_like_command(clean_command):
                        commands.append(clean_command)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_commands = []
        for cmd in commands:
            if cmd not in seen:
                seen.add(cmd)
                unique_commands.append(cmd)
        
        return unique_commands
    
    def _clean_command(self, command: str) -> str:
        """Clean and normalize command"""
        # Remove common prefixes
        prefixes = ['$ ', '> ', '# ', 'sudo ']
        for prefix in prefixes:
            if command.startswith(prefix):
                command = command[len(prefix):]
                break
        
        # Remove trailing characters
        command = command.rstrip(';')
        
        return command.strip()
    
    def _looks_like_command(self, text: str) -> bool:
        """Determine if text looks like an executable command"""
        # Must not be too long or too short
        if len(text) < 2 or len(text) > 500:
            return False
        
        # Must start with a word (command name)
        if not re.match(r'^[a-zA-Z0-9_.-]+', text):
            return False
        
        # Common command indicators
        command_indicators = [
            # Common Unix commands
            r'^(ls|cat|grep|find|mkdir|touch|cp|mv|rm|chmod|chown)\b',
            # Package managers
            r'^(pip|npm|yarn|apt|yum|brew)\b',
            # Development tools
            r'^(git|python|node|docker|kubectl)\b',
            # System tools
            r'^(ps|top|netstat|systemctl|service)\b',
        ]
        
        return any(re.match(pattern, text) for pattern in command_indicators)
    
    async def _analyze_command_safety(self, command: str) -> CommandAnalysis:
        """Analyze command for safety and security risks"""
        warnings = []
        suggestions = []
        risk_level = "low"
        is_safe = True
        
        # Parse command to get base command
        try:
            parsed = shlex.split(command)
            if not parsed:
                return CommandAnalysis(False, "high", "invalid", ["Empty command"], [])
            
            base_command = parsed[0]
            args = parsed[1:] if len(parsed) > 1 else []
        except ValueError as e:
            return CommandAnalysis(False, "high", "parsing_error", 
                                 [f"Command parsing failed: {e}"], 
                                 ["Check command syntax"])
        
        # Check against forbidden commands
        if any(forbidden in command for forbidden in self.forbidden_commands):
            return CommandAnalysis(False, "critical", "destructive", 
                                 ["Destructive command detected"], 
                                 ["Use safer alternatives"])
        
        # Check whitelist if enabled
        if self.enable_whitelist and base_command not in self.allowed_commands:
            is_safe = False
            risk_level = "high"
            warnings.append(f"Command '{base_command}' not in whitelist")
            suggestions.append("Request whitelist addition for legitimate commands")
        
        # Analyze risk level based on command
        if base_command in self.high_risk_commands:
            risk_level = "high" if risk_level != "critical" else "critical"
            warnings.append(f"High-risk command: {base_command}")
            
            # Specific checks for high-risk commands
            if base_command == 'rm':
                if '-rf' in command or '-r' in args and '-f' in args:
                    risk_level = "critical"
                    warnings.append("Recursive force deletion detected")
                    if '/' in command or '*' in command:
                        is_safe = False
                        warnings.append("Dangerous path patterns in rm command")
            
            elif base_command == 'chmod':
                if '777' in args or '666' in args:
                    warnings.append("Overly permissive file permissions")
                    suggestions.append("Use minimal required permissions")
            
            elif base_command in ['wget', 'curl']:
                if any(url.startswith(('http://', 'https://')) for url in args):
                    warnings.append("Network download detected")
                    suggestions.append("Verify download sources")
        
        # Check for suspicious patterns
        suspicious_patterns = [
            (r'&\s*$', "Background execution"),
            (r'\|\s*bash', "Piped to bash execution"),
            (r'>\s*/dev/', "Output redirection to device"),
            (r'eval\s*\(', "Dynamic code evaluation"),
            (r'\$\([^)]*\)', "Command substitution"),
        ]
        
        for pattern, description in suspicious_patterns:
            if re.search(pattern, command):
                if risk_level == "low":
                    risk_level = "medium"
                warnings.append(f"Suspicious pattern: {description}")
        
        # Determine purpose
        purpose = self._determine_command_purpose(base_command, args)
        
        # Final safety determination
        if risk_level == "critical" or len(warnings) >= 3:
            is_safe = False
        
        return CommandAnalysis(
            is_safe=is_safe,
            risk_level=risk_level,
            purpose=purpose,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _determine_command_purpose(self, base_command: str, args: List[str]) -> str:
        """Determine the purpose of a command"""
        purposes = {
            'ls': 'file_listing',
            'cat': 'file_reading',
            'grep': 'text_search',
            'find': 'file_search',
            'mkdir': 'directory_creation',
            'touch': 'file_creation',
            'cp': 'file_copy',
            'mv': 'file_move',
            'rm': 'file_deletion',
            'chmod': 'permission_change',
            'chown': 'ownership_change',
            'git': 'version_control',
            'python': 'script_execution',
            'pip': 'package_management',
            'npm': 'package_management',
            'docker': 'containerization',
            'ps': 'process_listing',
            'kill': 'process_control',
            'systemctl': 'service_control',
        }
        
        return purposes.get(base_command, 'unknown')
    
    async def _execute_command_safely(self, command: str, analysis: CommandAnalysis) -> CommandResult:
        """Execute command with safety measures and monitoring"""
        start_time = time.time()
        
        try:
            logger.info(f"🚀 Executing: {command}")
            
            # Set up execution environment
            env = os.environ.copy()
            cwd = self.agent.project_folder_path or os.getcwd()
            
            # Execute command with timeout
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=self.max_timeout
                )
                
                execution_time = time.time() - start_time
                
                result = CommandResult(
                    command=command,
                    success=process.returncode == 0,
                    stdout=stdout.decode('utf-8', errors='replace'),
                    stderr=stderr.decode('utf-8', errors='replace'),
                    returncode=process.returncode,
                    execution_time=execution_time,
                    security_check=analysis.risk_level
                )
                
                # Add to history
                self._add_to_history(result)
                
                if result.success:
                    logger.info(f"✅ Command completed successfully in {execution_time:.2f}s")
                else:
                    logger.warning(f"⚠️ Command failed with return code {process.returncode}")
                
                return result
                
            except asyncio.TimeoutError:
                # Kill the process
                process.kill()
                await process.wait()
                
                execution_time = time.time() - start_time
                result = CommandResult(
                    command=command,
                    success=False,
                    stdout="",
                    stderr=f"Command timed out after {self.max_timeout} seconds",
                    returncode=-1,
                    execution_time=execution_time,
                    security_check=analysis.risk_level
                )
                
                self._add_to_history(result)
                logger.error(f"⏰ Command timed out after {self.max_timeout}s")
                return result
                
        except Exception as e:
            execution_time = time.time() - start_time
            result = CommandResult(
                command=command,
                success=False,
                stdout="",
                stderr=f"Execution error: {str(e)}",
                returncode=-1,
                execution_time=execution_time,
                security_check=analysis.risk_level
            )
            
            self._add_to_history(result)
            logger.error(f"❌ Command execution error: {e}")
            return result
    
    def _add_to_history(self, result: CommandResult) -> None:
        """Add command result to execution history"""
        self.execution_history.append(result)
        
        # Maintain history size limit
        if len(self.execution_history) > self.max_history:
            self.execution_history = self.execution_history[-self.max_history:]
    
    def _generate_execution_summary(self, results: List[CommandResult]) -> str:
        """Generate summary of command execution results"""
        if not results:
            return ""
        
        summary = "\n\n⚡ COMMAND EXECUTION SUMMARY:\n" + "="*50 + "\n"
        
        total_commands = len(results)
        successful_commands = sum(1 for r in results if r.success)
        total_time = sum(r.execution_time for r in results)
        
        summary += f"📊 EXECUTION STATISTICS:\n"
        summary += f"• Commands executed: {total_commands}\n"
        summary += f"• Successful: {successful_commands}/{total_commands}\n"
        summary += f"• Total execution time: {total_time:.2f} seconds\n"
        summary += f"• Average time per command: {total_time/total_commands:.2f} seconds\n\n"
        
        for i, result in enumerate(results, 1):
            summary += f"🔧 COMMAND {i}: {result.command[:60]}{'...' if len(result.command) > 60 else ''}\n"
            summary += f"• Status: {'✅ SUCCESS' if result.success else '❌ FAILED'}\n"
            summary += f"• Return Code: {result.returncode}\n"
            summary += f"• Execution Time: {result.execution_time:.2f}s\n"
            summary += f"• Security Level: {result.security_check.upper()}\n"
            
            if result.stdout:
                stdout_preview = result.stdout[:200].replace('\n', ' ')
                summary += f"• Output: {stdout_preview}{'...' if len(result.stdout) > 200 else ''}\n"
            
            if result.stderr and not result.success:
                stderr_preview = result.stderr[:100].replace('\n', ' ')
                summary += f"• Error: {stderr_preview}{'...' if len(result.stderr) > 100 else ''}\n"
            
            summary += "\n" + "-"*30 + "\n"
        
        # Security summary
        risk_levels = [r.security_check for r in results]
        if any(level in ['high', 'critical'] for level in risk_levels):
            summary += "🔒 SECURITY NOTICE:\n"
            summary += "Some commands were flagged as high-risk. Review execution logs.\n"
            summary += "Always verify command safety in production environments.\n\n"
        
        return summary
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get comprehensive execution statistics"""
        if not self.execution_history:
            return {"message": "No command execution history available"}
        
        successful = [r for r in self.execution_history if r.success]
        failed = [r for r in self.execution_history if not r.success]
        
        # Command frequency analysis
        command_freq = {}
        for result in self.execution_history:
            base_cmd = result.command.split()[0] if result.command.split() else 'unknown'
            command_freq[base_cmd] = command_freq.get(base_cmd, 0) + 1
        
        # Risk level distribution
        risk_distribution = {}
        for result in self.execution_history:
            risk_distribution[result.security_check] = risk_distribution.get(result.security_check, 0) + 1
        
        return {
            "total_executions": len(self.execution_history),
            "success_rate": len(successful) / len(self.execution_history),
            "average_execution_time": sum(r.execution_time for r in self.execution_history) / len(self.execution_history),
            "command_frequency": dict(sorted(command_freq.items(), key=lambda x: x[1], reverse=True)[:10]),
            "risk_distribution": risk_distribution,
            "recent_failures": [{"command": r.command, "error": r.stderr} for r in failed[-5:]],
            "most_used_commands": list(dict(sorted(command_freq.items(), key=lambda x: x[1], reverse=True)[:5]).keys())
        }