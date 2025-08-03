import ollama
import asyncio
import subprocess
from typing import Optional, Any
import re
import os

from agents.base_agent import BaseAgent, AgentMessage

class WorkerAgent(BaseAgent):
    def __init__(self, agent_id: str, name: str, model: str = "llama3", project_folder_path: Optional[str] = None):
        super().__init__(agent_id, name)
        self.model = model
        self.project_folder_path = project_folder_path

    async def _perform_task(self, prompt: str) -> str:
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
            return response["message"]["content"]
        except Exception as e:
            print(f"Error performing task: {e}")
            raise

    async def _run_command(self, command: str) -> str:
        print(f"[WorkerAgent {self.name}] Executing command: {command}")
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.project_folder_path if self.project_folder_path else None
        )
        stdout, stderr = await process.communicate()

        output = ""
        if stdout:
            output += f"Stdout:\n{stdout.decode().strip()}\n"
        if stderr:
            output += f"Stderr:\n{stderr.decode().strip()}\n"
        if process.returncode != 0:
            output += f"Error: Command exited with code {process.returncode}\n"
        return output.strip()

    async def _handle_file_saving(self, message_content: str, result: str) -> str:
        save_message = ""
        
        # Enhanced regex patterns for file saving with German and English support
        save_patterns = [
            r"(?:speichere sie (?:im Projektordner )?(?:unter|als))\s+([\w\.-]+)",
            r"(?:save it (?:to|as))\s+([\w\.-]+)",
            r"(?:erstelle|create).*?(?:als|as)\s+([\w\.-]+)",
            r"(?:datei|file).*?([\w\.-]+\.py)",
            r"(app\.py|[\w\.-]+\.py)"  # Match any .py file mentioned
        ]
        
        save_match = None
        for pattern in save_patterns:
            save_match = re.search(pattern, message_content, re.IGNORECASE)
            if save_match:
                break
        
        # Also check if this is a Flask app task specifically
        if not save_match and ("flask" in message_content.lower() or "hello world" in message_content.lower()):
            save_match = type('Match', (), {'group': lambda self, x: 'app.py'})()

        if save_match and self.project_folder_path:
            target_path = save_match.group(1).strip()
            full_path = os.path.join(self.project_folder_path, target_path)

            # Enhanced code extraction from result
            content_to_write = self._extract_code_content(result)

            try:
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding='utf-8') as f:
                    f.write(content_to_write)
                save_message = f"\n✅ File saved to: {full_path}"
                print(save_message)
            except Exception as e:
                save_message = f"\n❌ Error saving file to {full_path}: {e}"
                print(save_message)
        
        return save_message
    
    def _extract_code_content(self, result: str) -> str:
        """Extract code content from LLM response"""
        # Try to extract code from markdown code blocks
        code_patterns = [
            r"```python\s*\n(.*?)\n```",
            r"```\s*\n(.*?)\n```",
            r"```(.+?)```"
        ]
        
        for pattern in code_patterns:
            match = re.search(pattern, result, re.DOTALL)
            if match:
                code_content = match.group(1).strip()
                if code_content and len(code_content) > 10:  # Reasonable code length
                    return code_content
        
        # If no code blocks found, check if result contains Flask-like code
        if "from flask import" in result.lower() or "app = flask" in result.lower() or "@app.route" in result.lower():
            # Extract everything that looks like Python code
            lines = result.split('\n')
            code_lines = []
            in_code = False
            
            for line in lines:
                stripped_line = line.strip()
                if (stripped_line.startswith(('from ', 'import ', 'def ', 'class ', 'if ', '@', 'app.')) or
                    '=' in stripped_line or 'return' in stripped_line):
                    in_code = True
                    code_lines.append(line)
                elif in_code and (stripped_line == '' or stripped_line.startswith(' ')):
                    code_lines.append(line)
                elif in_code and not stripped_line.startswith('#'):
                    # End of code block
                    break
            
            if code_lines:
                return '\n'.join(code_lines)
        
        # Fallback: use entire result but clean it up
        cleaned_result = result.strip()
        
        # Remove common LLM response prefixes/suffixes
        prefixes_to_remove = [
            "Here's the Flask application:",
            "Here is the Flask app:",
            "This is a simple Flask application:",
            "Here's a basic Flask app:",
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned_result.lower().startswith(prefix.lower()):
                cleaned_result = cleaned_result[len(prefix):].strip()
                break
        
        return cleaned_result

    async def _handle_command_execution(self, message_content: str) -> str:
        command_output = ""
        command_match = re.search(r"(?:führe den befehl aus|execute command):\s*(.+)", message_content, re.IGNORECASE)
        if command_match:
            command_to_execute = command_match.group(1).strip()
            command_output = await self._run_command(command_to_execute)
        return command_output

    async def _analyze_and_execute_task(self, task: str) -> str:
        """Analyze task and decide whether to use LLM or direct command execution"""
        # Enhanced command execution prompts for better AI understanding
        enhanced_prompt = f"""
You are an AI assistant with command-line access. Analyze this task and provide the most efficient solution:

Task: {task}

You have the following capabilities:
1. Create files using standard commands (echo, cat, touch, etc.)
2. Execute Python scripts and install packages
3. Use any command-line tools available on the system
4. Generate code and save it to files

For this task, please:
1. First, analyze what needs to be done
2. Then provide the specific commands to execute
3. If code generation is needed, create the code and save it to the appropriate file

Be practical and use command-line tools effectively. Respond with clear steps and commands.
"""
        
        # Get AI response with enhanced prompt
        result = await self._perform_task(enhanced_prompt)
        
        # Parse and execute any commands found in the response
        await self._parse_and_execute_commands(result)
        
        return result

    async def _parse_and_execute_commands(self, ai_response: str) -> str:
        """Parse AI response for commands and execute them"""
        command_output = ""
        
        # Look for command blocks in various formats
        command_patterns = [
            r"```bash\s*\n(.*?)\n```",
            r"```shell\s*\n(.*?)\n```", 
            r"```\s*\n(.*?)\n```",
            r"Command:\s*`([^`]+)`",
            r"Execute:\s*`([^`]+)`",
            r"Run:\s*`([^`]+)`"
        ]
        
        commands_found = []
        for pattern in command_patterns:
            matches = re.findall(pattern, ai_response, re.DOTALL | re.IGNORECASE)
            for match in matches:
                # Split multi-line commands
                cmd_lines = [line.strip() for line in match.split('\n') if line.strip()]
                commands_found.extend(cmd_lines)
        
        # Execute found commands
        for command in commands_found:
            if command and not command.startswith('#'):  # Skip comments
                print(f"[WorkerAgent {self.name}] Executing AI-suggested command: {command}")
                try:
                    cmd_result = await self._run_command(command)
                    command_output += f"\n--- Command: {command} ---\n{cmd_result}\n"
                except Exception as e:
                    command_output += f"\n--- Command: {command} (FAILED) ---\n{str(e)}\n"
        
        return command_output

    async def receive_message(self, message: AgentMessage):
        print(f"Agent {self.name} ({self.agent_id}) received message from {message.sender_id}: {message.content}")

        # Use AI analysis and command execution approach
        result = await self._analyze_and_execute_task(message.content)
        
        print(f"Agent {self.name} ({self.agent_id}) completed task analysis")

        # Handle file saving and additional command execution
        save_message = await self._handle_file_saving(message.content, result)
        command_output = await self._handle_command_execution(message.content)

        final_response = result + save_message
        if command_output:
            final_response += f"\nCommand Output:\n{command_output}"

        await self.send_message(message.sender_id, "response", final_response, message.request_id)