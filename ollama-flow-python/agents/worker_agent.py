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
            response = await ollama.chat(
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

    async def receive_message(self, message: AgentMessage):
        print(f"Agent {self.name} ({self.agent_id}) received message from {message.sender_id}: {message.content}")

        result = await self._perform_task(message.content)
        print(f"Agent {self.name} ({self.agent_id}) completed task with result: {result}")

        save_message = ""
        save_match = re.search(r"(?:speichere sie (?:im Projektordner )?unter|speichere sie als)\s+(.+?)(?:\s+ab)?$", message.content, re.IGNORECASE)

        if save_match and self.project_folder_path:
            target_path = save_match.group(1).strip()
            full_path = os.path.join(self.project_folder_path, target_path)

            code_block_match = re.search(r"```[\s\S]*?\n([\s\S]*?)\n```", result)
            content_to_write = code_block_match.group(1) if code_block_match else result

            try:
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w") as f:
                    f.write(content_to_write)
                save_message = f"\nFile saved to: {full_path}"
                print(save_message)
            except Exception as e:
                save_message = f"\nError saving file to {full_path}: {e}"
                print(save_message)

        # Check for shell command execution instruction
        command_match = re.search(r"(?:führe den befehl aus|execute command):\s*(.+)", message.content, re.IGNORECASE)
        if command_match:
            command_to_execute = command_match.group(1).strip()
            command_output = await self._run_command(command_to_execute)
            result += f"\nCommand Output:\n{command_output}"

        await self.send_message(message.sender_id, "response", result + save_message, message.request_id)
