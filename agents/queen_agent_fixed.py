import asyncio
import json
from typing import List, Type, Optional

from agents.base_agent import BaseAgent, AgentMessage
from agents.sub_queen_agent import SubQueenAgent
from agents.worker_agent import WorkerAgent
from llm_backend import EnhancedLLMBackendManager

class QueenAgent(BaseAgent):
    def __init__(self, agent_id: str, name: str, architecture_type: str, model: str = "llama3"):
        super().__init__(agent_id, name)
        self.architecture_type = architecture_type
        self.model = model
        self.sub_queen_agents: List[BaseAgent] = []
        self.worker_agents: List[BaseAgent] = []
        self.current_sub_queen_index = 0
        self.current_worker_index = 0
        self.backend_manager = None  # Will be set by orchestrator
        
        # Track active tasks and responses - THIS IS THE KEY FIX
        self.active_tasks = {}
        self.completed_requests = set()  # Prevent duplicate responses

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
            response = await self.backend_manager.generate(
                prompt=decomposition_prompt,
                model=self.model
            )
            raw_response = response.content
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
        print(f"[QueenAgent FIXED] {self.name} received message from {message.sender_id}")
        print(f"[QueenAgent FIXED] Message type: {message.message_type}, Request ID: {message.request_id}")

        # Prevent duplicate processing
        if message.request_id in self.completed_requests:
            print(f"[QueenAgent FIXED] Ignoring duplicate request {message.request_id}")
            return

        if message.message_type == "task":
            print(f"[QueenAgent FIXED] Processing task: {message.content}")
            subtasks = await self._decompose_task(message.content)
            print(f"[QueenAgent FIXED] Decomposed into {len(subtasks)} subtasks")

            # Initialize task tracking - THIS IS THE CRITICAL FIX
            self.active_tasks[message.request_id] = {
                'subtasks': subtasks,
                'responses': [],
                'expected_count': len(subtasks),
                'original_task': message.content
            }
            print(f"[QueenAgent FIXED] Task tracking initialized for {message.request_id}: expecting {len(subtasks)} responses")

            # Delegate tasks to workers
            for i, subtask in enumerate(subtasks):
                if self.architecture_type in ['CENTRALIZED', 'FULLY_CONNECTED']:
                    if not self.worker_agents:
                        print("[QueenAgent FIXED] No workers available!")
                        await self.send_message("orchestrator", "final-error", "No WorkerAgents available.", message.request_id)
                        return

                    target_worker = self.worker_agents[self.current_worker_index]
                    self.current_worker_index = (self.current_worker_index + 1) % len(self.worker_agents)

                    delegated_task = f"Delegated task from Queen to {target_worker.name}: {subtask}"
                    print(f"[QueenAgent FIXED] Delegating to {target_worker.name}")
                    await self.send_message(target_worker.agent_id, "sub-task", delegated_task, message.request_id)

        elif message.message_type == "response":
            print(f"[QueenAgent FIXED] Received worker response from {message.sender_id}")
            await self._handle_worker_response(message)

    async def _handle_worker_response(self, message: AgentMessage):
        """Handle worker responses and wait for all before sending final response"""
        request_id = message.request_id
        
        if request_id not in self.active_tasks:
            print(f"[QueenAgent FIXED] ERROR: No task tracking for {request_id}")
            # Don't send immediate response - this was the bug!
            return
        
        if request_id in self.completed_requests:
            print(f"[QueenAgent FIXED] Task {request_id} already completed, ignoring response")
            return

        task_info = self.active_tasks[request_id]
        task_info['responses'].append({
            'sender': message.sender_id,
            'content': message.content
        })
        
        responses_count = len(task_info['responses'])
        expected_count = task_info['expected_count']
        print(f"[QueenAgent FIXED] Response {responses_count}/{expected_count} received for {request_id}")
        
        # Only send final response when ALL workers have responded
        if responses_count >= expected_count:
            print(f"[QueenAgent FIXED] All {expected_count} workers completed! Sending final response")
            
            # Aggregate all responses
            aggregated_response = f"Task: {task_info['original_task']}\n\n"
            aggregated_response += "=== COMPLETED SUBTASKS ===\n"
            
            for i, subtask in enumerate(task_info['subtasks']):
                aggregated_response += f"\n--- Subtask {i+1}: {subtask} ---\n"
                if i < len(task_info['responses']):
                    worker_response = task_info['responses'][i]
                    aggregated_response += f"Worker: {worker_response['sender']}\n"
                    aggregated_response += f"Result: {worker_response['content'][:200]}...\n"
                else:
                    aggregated_response += "Status: No response received\n"
            
            aggregated_response += f"\n=== SUMMARY ===\n"
            aggregated_response += f"Total subtasks: {len(task_info['subtasks'])}\n"
            aggregated_response += f"Completed responses: {len(task_info['responses'])}\n"
            
            # Mark as completed to prevent duplicates
            self.completed_requests.add(request_id)
            
            # Send final aggregated response
            await self.send_message("orchestrator", "final-response", aggregated_response, request_id)
            
            # Clean up
            del self.active_tasks[request_id]
        else:
            print(f"[QueenAgent FIXED] Waiting for {expected_count - responses_count} more responses...")
