import ollama
import asyncio
import json
from typing import List, Type, Optional

from agents.base_agent import BaseAgent, AgentMessage
from agents.sub_queen_agent import SubQueenAgent
from agents.worker_agent import WorkerAgent

class QueenAgent(BaseAgent):
    def __init__(self, agent_id: str, name: str, architecture_type: str, model: str = "llama3"):
        super().__init__(agent_id, name)
        self.architecture_type = architecture_type
        self.model = model
        self.sub_queen_agents: List[BaseAgent] = []
        self.worker_agents: List[BaseAgent] = []
        self.current_sub_queen_index = 0
        self.current_worker_index = 0

    def initialize_agents(self):
        if self.orchestrator:
            if self.architecture_type == 'HIERARCHICAL':
                self.sub_queen_agents = self.orchestrator.get_agents_by_type(SubQueenAgent)
                print(f"QueenAgent {self.name} found {len(self.sub_queen_agents)} SubQueenAgents.")
            elif self.architecture_type in ['CENTRALIZED', 'FULLY_CONNECTED']:
                self.worker_agents = self.orchestrator.get_agents_by_type(WorkerAgent)
                print(f"QueenAgent {self.name} found {len(self.worker_agents)} WorkerAgents.")

    async def _decompose_task(self, task: str) -> List[str]:
        decomposition_prompt = f"Given the main task: '{task}'. Decompose this into a list of smaller, actionable subtasks. Respond only with a JSON array of strings, where each string is a subtask. Example: ['Subtask 1', 'Subtask 2']"
        try:
            response = await ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": decomposition_prompt}],
            )
            raw_response = response["message"]["content"]
            print(f"[QueenAgent] Decomposition LLM Raw Response: {raw_response}")
            try:
                subtasks = json.loads(raw_response)
                if isinstance(subtasks, list) and all(isinstance(item, str) for item in subtasks):
                    return subtasks
                else:
                    print(f"[QueenAgent] LLM response is not a valid JSON array of strings. Falling back to single task.")
                    return [task]
            except json.JSONDecodeError as e:
                print(f"[QueenAgent] JSON parsing failed: {e}. Falling back to single task.")
                return [task]
        except Exception as e:
            print(f"[QueenAgent] Error during task decomposition: {e}. Falling back to single task.")
            return [task]

    async def receive_message(self, message: AgentMessage):
        print(f"QueenAgent {self.name} ({self.agent_id}) received message from {message.sender_id}: {message.content}")

        if message.message_type == "task":
            subtasks = await self._decompose_task(message.content)
            print(f"[QueenAgent] Decomposed into subtasks: {subtasks}")

            for subtask in subtasks:
                if self.architecture_type == 'HIERARCHICAL':
                    if not self.sub_queen_agents:
                        print("No SubQueenAgents available to delegate tasks.")
                        await self.send_message("orchestrator", "final-error", "No SubQueenAgents available.", message.request_id)
                        return

                    target_sub_queen = self.sub_queen_agents[self.current_sub_queen_index]
                    self.current_sub_queen_index = (self.current_sub_queen_index + 1) % len(self.sub_queen_agents)

                    delegated_task = f"Delegated task from Main Queen to {target_sub_queen.name}: {subtask}"
                    print(f"QueenAgent delegating task to {target_sub_queen.name} ({target_sub_queen.agent_id})")
                    await self.send_message(target_sub_queen.agent_id, "sub-task-to-subqueen", delegated_task, message.request_id)
                elif self.architecture_type in ['CENTRALIZED', 'FULLY_CONNECTED']:
                    if not self.worker_agents:
                        print("No WorkerAgents available to delegate tasks.")
                        await self.send_message("orchestrator", "final-error", "No WorkerAgents available.", message.request_id)
                        return

                    target_worker = self.worker_agents[self.current_worker_index]
                    self.current_worker_index = (self.current_worker_index + 1) % len(self.worker_agents)

                    delegated_task = f"Delegated task from Queen to {target_worker.name}: {subtask}"
                    print(f"QueenAgent delegating task to {target_worker.name} ({target_worker.agent_id})")
                    await self.send_message(target_worker.agent_id, "sub-task", delegated_task, message.request_id)

        elif message.message_type == "group-response":
            print(f"QueenAgent received group response from {message.sender_id}: {message.content}")
            await self.send_message("orchestrator", "final-response", f"Aggregated response from {message.content['from_sub_queen']}: {message.content['content']}", message.request_id)
        elif message.message_type == "response":
            print(f"QueenAgent received direct response from {message.sender_id}: {message.content}")
            await self.send_message("orchestrator", "final-response", f"Response from {message.sender_id}: {message.content}", message.request_id)
        elif message.message_type == "error":
            print(f"QueenAgent received error from {message.sender_id}: {message.content}")
            await self.send_message("orchestrator", "final-error", f"Error from {message.sender_id}: {message.content}", message.request_id)
