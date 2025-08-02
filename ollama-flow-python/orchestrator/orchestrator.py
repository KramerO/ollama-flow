from typing import Dict, Any, Type, List, Optional
from agents.base_agent import BaseAgent, AgentMessage
import asyncio
import uuid

class Orchestrator:
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.response_resolvers: Dict[str, asyncio.Future] = {}
        self.request_counter = 0

    def register_agent(self, agent: BaseAgent):
        if agent.agent_id in self.agents:
            print(f"Warning: Agent with ID {agent.agent_id} already registered. Overwriting.")
        self.agents[agent.agent_id] = agent
        agent.set_orchestrator(self)
        print(f"Agent {agent.name} ({agent.agent_id}) registered.")

    async def dispatch_message(self, message: AgentMessage):
        print(f"[Orchestrator.dispatch_message] Received message. Sender: {message.sender_id}, Receiver: {message.receiver_id}, Type: {message.message_type}, RequestId: {message.request_id}")

        if message.receiver_id == "orchestrator":
            print(f"[Orchestrator.dispatch_message] Handling message for orchestrator. Type: {message.message_type}, Sender: {message.sender_id}, RequestId: {message.request_id}")
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
            return

        receiver = self.agents.get(message.receiver_id)
        if receiver:
            print(f"Dispatching message from {message.sender_id} to {message.receiver_id}")
            await receiver.receive_message(message)
        else:
            print(f"Error: Agent with ID {message.receiver_id} not found.")

    def get_agents_by_type(self, agent_type: Type[BaseAgent]) -> List[BaseAgent]:
        return [agent for agent in self.agents.values() if isinstance(agent, agent_type)]

    async def run(self, prompt: str) -> str:
        print(f"Orchestrator received prompt: {prompt}")
        
        # For now, directly send to a QueenAgent (assuming one exists)
        # In a more complex setup, this would involve initial task routing
        queen_agents = self.get_agents_by_type(BaseAgent) # Placeholder, will be QueenAgent
        if not queen_agents:
            return "Error: No QueenAgent registered."
        
        target_receiver_id = queen_agents[0].agent_id # Assuming the first registered agent is the Queen

        request_id = f"request-{self.request_counter}"
        self.request_counter += 1

        initial_message = AgentMessage("orchestrator", target_receiver_id, "task", prompt, request_id)

        future = asyncio.Future()
        self.response_resolvers[request_id] = future

        await self.dispatch_message(initial_message)

        return await future
