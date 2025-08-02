import ollama
import asyncio
import json
from typing import List, Type, Optional

from agents.base_agent import BaseAgent, AgentMessage
from agents.worker_agent import WorkerAgent

class SubQueenAgent(BaseAgent):
    def __init__(self, agent_id: str, name: str, model: str = "llama3"):
        super().__init__(agent_id, name)
        self.model = model
        self.group_worker_agents: List[WorkerAgent] = []
        self.current_agent_index = 0

    def initialize_group_agents(self, agents: List[WorkerAgent]):
        self.group_worker_agents = agents
        print(f"SubQueenAgent {self.name} initialized with {len(self.group_worker_agents)} WorkerAgents.")

    async def _decompose_task(self, task: str) -> List[str]:
        decomposition_prompt = f"Given the sub-task: '{task}'. Decompose this into a list of smaller, actionable subtasks for a WorkerAgent. Respond only with a JSON array of strings, where each string is a subtask. Example: ['Subtask 1', 'Subtask 2']"
        try:
            response = await ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": decomposition_prompt}],
            )
            raw_response = response["message"]["content"]
            print(f"[SubQueenAgent] Decomposition LLM Raw Response: {raw_response}")
            try:
                subtasks = json.loads(raw_response)
                if isinstance(subtasks, list) and all(isinstance(item, str) for item in subtasks):
                    return subtasks
                else:
                    print(f"[SubQueenAgent] LLM response is not a valid JSON array of strings. Falling back to single task.")
                    return [task]
            except json.JSONDecodeError as e:
                print(f"[SubQueenAgent] JSON parsing failed: {e}. Falling back to single task.")
                return [task]
        except Exception as e:
            print(f"[SubQueenAgent] Error during task decomposition: {e}. Falling back to single task.")
            return [task]

    async def receive_message(self, message: AgentMessage):
        print(f"SubQueenAgent {self.name} ({self.agent_id}) received message from {message.sender_id}: {message.content}")

        if message.message_type == "sub-task-to-subqueen":
            subtasks = await self._decompose_task(message.content)
            print(f"[SubQueenAgent] Decomposed into subtasks: {subtasks}")

            for subtask in subtasks:
                if not self.group_worker_agents:
                    print(f"SubQueenAgent {self.name}: No WorkerAgents in group to delegate tasks.")
                    await self.send_message(message.sender_id, "error", f"No WorkerAgents in group for {self.name}", message.request_id)
                    return

                target_worker = self.group_worker_agents[self.current_agent_index]
                self.current_agent_index = (self.current_agent_index + 1) % len(self.group_worker_agents)

                delegated_task = f"Delegated by {self.name} to {target_worker.name}: {subtask}"
                print(f"SubQueenAgent {self.name} delegating task to {target_worker.name} ({target_worker.agent_id})")
                await self.send_message(target_worker.agent_id, "sub-task", delegated_task, message.request_id)

        elif message.message_type == "response" or message.message_type == "error":
            print(f"SubQueenAgent {self.name} received {message.message_type} from {message.sender_id}: {message.content}")
            await self.send_message("queen-agent-1", "group-response", {
                "from_sub_queen": self.agent_id,
                "original_sender": message.sender_id,
                "type": message.message_type,
                "content": message.content,
            }, message.request_id)
