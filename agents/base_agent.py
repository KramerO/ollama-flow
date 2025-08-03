from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio

class AgentMessage:
    def __init__(self, sender_id: str, receiver_id: str, message_type: str, content: Any, request_id: Optional[str] = None, message_id: Optional[int] = None):
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.message_type = message_type
        self.content = content
        self.request_id = request_id
        self.message_id = message_id # Added for database message ID

    def to_dict(self):
        return {
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "message_type": self.message_type,
            "content": self.content,
            "request_id": self.request_id,
            "message_id": self.message_id
        }

class BaseAgent(ABC):
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.orchestrator = None
        self.db_manager = None
        self.polling_task = None

    def set_orchestrator(self, orchestrator):
        self.orchestrator = orchestrator

    def set_db_manager(self, db_manager):
        self.db_manager = db_manager
        if self.polling_task is None:
            self.polling_task = asyncio.create_task(self._message_polling_task())

    @abstractmethod
    async def receive_message(self, message: AgentMessage):
        pass

    async def send_message(self, receiver_id: str, message_type: str, content: Any, request_id: Optional[str] = None):
        if not self.db_manager:
            print(f"Agent {self.name} ({self.agent_id}) cannot send message: DB Manager not set.")
            return
        
        message_id = self.db_manager.insert_message(self.agent_id, receiver_id, message_type, content, request_id)
        print(f"Agent {self.name} ({self.agent_id}) sent message to {receiver_id} (ID: {message_id})")

    async def _message_polling_task(self):
        while True:
            try:
                messages = self.db_manager.get_pending_messages(self.agent_id)
                for msg_data in messages:
                    message = AgentMessage(
                        sender_id=msg_data['sender_id'],
                        receiver_id=msg_data['receiver_id'],
                        message_type=msg_data['type'],
                        content=msg_data['content'],
                        request_id=msg_data['request_id'],
                        message_id=msg_data['id']
                    )
                    print(f"Agent {self.name} ({self.agent_id}) received message from DB: {message.sender_id} -> {message.receiver_id} ({message.message_type})")
                    await self.receive_message(message)
                    self.db_manager.mark_message_as_processed(message.message_id)
            except Exception as e:
                print(f"Error in agent {self.name} ({self.agent_id}) polling task: {e}")
            await asyncio.sleep(0.1) # Poll every 100ms
