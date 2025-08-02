import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import os

from agents.worker_agent import WorkerAgent
from agents.base_agent import AgentMessage

class TestWorkerAgent(unittest.TestCase):

    def setUp(self):
        self.mock_orchestrator = AsyncMock()
        self.project_folder = "/tmp/test_project"
        self.worker_agent = WorkerAgent("worker-1", "Test Worker", project_folder_path=self.project_folder)
        self.worker_agent.set_orchestrator(self.mock_orchestrator)

    async def test_perform_task(self):
        with patch('ollama.chat', new_callable=AsyncMock) as mock_ollama_chat:
            mock_ollama_chat.return_value = {"message": {"content": "Ollama response"}}
            response = await self.worker_agent._perform_task("Test prompt")
            self.assertEqual(response, "Ollama response")
            mock_ollama_chat.assert_called_once_with(
                model="llama3",
                messages=[{"role": "user", "content": "Test prompt"}],
            )

    async def test_run_command(self):
        with patch('asyncio.create_subprocess_shell', new_callable=AsyncMock) as mock_subprocess_shell:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"stdout output", b"stderr output")
            mock_process.returncode = 0
            mock_subprocess_shell.return_value = mock_process

            command_output = await self.worker_agent._run_command("ls -la")
            self.assertIn("Stdout:\nstdout output", command_output)
            self.assertIn("Stderr:\nstderr output", command_output)
            mock_subprocess_shell.assert_called_once_with(
                "ls -la",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_folder
            )

    async def test_receive_message_no_save_no_command(self):
        with patch('ollama.chat', new_callable=AsyncMock) as mock_ollama_chat:
            with patch('builtins.open', MagicMock()):
                with patch('os.makedirs', MagicMock()):
                    with patch('os.path.join', MagicMock(side_effect=os.path.join)):

                        mock_ollama_chat.return_value = {"message": {"content": "Ollama response"}}
                        message = AgentMessage("sender", "worker-1", "task", "Just a prompt")
                        await self.worker_agent.receive_message(message)

                        mock_ollama_chat.assert_called_once()
                        self.mock_orchestrator.dispatch_message.assert_called_once_with(
                            AgentMessage("worker-1", "sender", "response", "Ollama response", None)
                        )
                        open.assert_not_called()
                        os.makedirs.assert_not_called()

    async def test_receive_message_with_save(self):
        with patch('ollama.chat', new_callable=AsyncMock) as mock_ollama_chat:
            with patch('builtins.open', MagicMock()) as mock_open:
                with patch('os.makedirs', MagicMock()) as mock_makedirs:
                    with patch('os.path.join', MagicMock(side_effect=os.path.join)):

                        mock_ollama_chat.return_value = {"message": {"content": "```python\nprint(\"Hello, World!\")\n```"}}
                        prompt = "Write a Python script and save it as app.py"
                        message = AgentMessage("sender", "worker-1", "task", prompt)
                        await self.worker_agent.receive_message(message)

                        mock_ollama_chat.assert_called_once()
                        mock_makedirs.assert_called_once_with(self.project_folder, exist_ok=True)
                        mock_open.assert_called_once_with(os.path.join(self.project_folder, "app.py"), "w")
                        mock_open.return_value.__enter__.return_value.write.assert_called_once_with("print(\"Hello, World!\")\n")
                        self.mock_orchestrator.dispatch_message.assert_called_once()
                        dispatched_message = self.mock_orchestrator.dispatch_message.call_args[0][0]
                        self.assertIn("File saved to:", dispatched_message.content)

    async def test_receive_message_with_command(self):
        with patch('ollama.chat', new_callable=AsyncMock) as mock_ollama_chat:
            with patch('asyncio.create_subprocess_shell', new_callable=AsyncMock) as mock_subprocess_shell:

                mock_ollama_chat.return_value = {"message": {"content": "Ollama response"}}
                mock_process = AsyncMock()
                mock_process.communicate.return_value = (b"command stdout", b"")
                mock_process.returncode = 0
                mock_subprocess_shell.return_value = mock_process

                prompt = "execute command: echo Hello"
                message = AgentMessage("sender", "worker-1", "task", prompt)
                await self.worker_agent.receive_message(message)

                mock_ollama_chat.assert_called_once()
                mock_subprocess_shell.assert_called_once_with(
                    "echo Hello",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=self.project_folder
                )
                self.mock_orchestrator.dispatch_message.assert_called_once()
                dispatched_message = self.mock_orchestrator.dispatch_message.call_args[0][0]
                self.assertIn("Command Output:\ncommand stdout", dispatched_message.content)

if __name__ == '__main__':
    unittest.main()