from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class AgentMessage:
    def __init__(self, sender_id: str, receiver_id: str, message_type: str, content: Any, request_id: Optional[str] = None):
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.message_type = message_type
        self.content = content
        self.request_id = request_id

    def to_dict(self):
        return {
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "message_type": self.message_type,
            "content": self.content,
            "request_id": self.request_id
        }

class BaseAgent(ABC):
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.orchestrator = None

    def set_orchestrator(self, orchestrator):
        self.orchestrator = orchestrator

    @abstractmethod
    async def receive_message(self, message: AgentMessage):
        pass

    async def send_message(self, receiver_id: str, message_type: str, content: Any, request_id: Optional[str] = None):
        if not self.orchestrator:
            print(f"Agent {self.name} ({self.agent_id}) cannot send message: Orchestrator not set.")
            return
        message = AgentMessage(self.agent_id, receiver_id, message_type, content, request_id)
        await self.orchestrator.dispatch_message(message)
