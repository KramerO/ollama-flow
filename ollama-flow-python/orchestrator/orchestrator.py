from typing import Dict, Any, Type, List, Optional
from agents.base_agent import BaseAgent, AgentMessage
import asyncio
import uuid
from db_manager import MessageDBManager # Import the new DB Manager

class Orchestrator:
    def __init__(self, db_manager: MessageDBManager):
        self.agents: Dict[str, BaseAgent] = {}
        self.response_resolvers: Dict[str, asyncio.Future] = {}
        self.request_counter = 0
        self.db_manager = db_manager
        self.polling_task = None

    def start_polling(self):
        if self.polling_task is None:
            self.polling_task = asyncio.create_task(self._orchestrator_polling_task())

    def register_agent(self, agent: BaseAgent):
        if agent.agent_id in self.agents:
            print(f"Warning: Agent with ID {agent.agent_id} already registered. Overwriting.")
        self.agents[agent.agent_id] = agent
        agent.set_orchestrator(self) # Still needed for final response handling
        agent.set_db_manager(self.db_manager)
        print(f"Agent {agent.name} ({agent.agent_id}) registered.")

    async def _orchestrator_polling_task(self):
        while True:
            try:
                messages = self.db_manager.get_pending_messages("orchestrator")
                for msg_data in messages:
                    message = AgentMessage(
                        sender_id=msg_data['sender_id'],
                        receiver_id=msg_data['receiver_id'],
                        message_type=msg_data['type'],
                        content=msg_data['content'],
                        request_id=msg_data['request_id'],
                        message_id=msg_data['id']
                    )
                    print(f"[Orchestrator.polling] Received message. Sender: {message.sender_id}, Type: {message.message_type}, RequestId: {message.request_id}")

                    request_id = message.request_id if message.request_id else message.sender_id
                    if message.message_type == "final-response":
                        if request_id in self.response_resolvers:
                            self.response_resolvers[request_id].set_result(message.content)
                            del self.response_resolvers[request_id]
                        else:
                            print(f"Warning: No resolver found for request_id {request_id}.")
                    elif message.message_type == "final-error":
                        if request_id in self.response_resolvers:
                            self.response_resolvers[request_id].set_exception(Exception(message.content))
                            del self.response_resolvers[request_id]
                        else:
                            print(f"Warning: No resolver found for request_id {request_id}.")
                    
                    self.db_manager.mark_message_as_processed(message.message_id)
            except Exception as e:
                print(f"Error in orchestrator polling task: {e}")
            await asyncio.sleep(0.1) # Poll every 100ms

    def get_agents_by_type(self, agent_type: Type[BaseAgent]) -> List[BaseAgent]:
        return [agent for agent in self.agents.values() if isinstance(agent, agent_type)]

    async def run(self, prompt: str) -> str:
        print(f"Orchestrator received prompt: {prompt}")
        
        # For now, directly send to a QueenAgent (assuming one exists)
        queen_agents = self.get_agents_by_type(BaseAgent) # Placeholder, will be QueenAgent
        if not queen_agents:
            return "Error: No QueenAgent registered."
        
        target_receiver_id = queen_agents[0].agent_id # Assuming the first registered agent is the Queen

        request_id = f"request-{self.request_counter}"
        self.request_counter += 1

        # Insert initial message into DB
        self.db_manager.insert_message("orchestrator", target_receiver_id, "task", prompt, request_id)
        print(f"Orchestrator inserted initial task for {target_receiver_id} (Request ID: {request_id})")

        future = asyncio.Future()
        self.response_resolvers[request_id] = future

        return await future
