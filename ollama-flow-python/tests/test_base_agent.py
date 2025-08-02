import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from agents.base_agent import BaseAgent, AgentMessage

class ConcreteAgent(BaseAgent):
    async def receive_message(self, message: AgentMessage):
        pass # Concrete implementation for testing

@pytest.fixture
def agent():
    return ConcreteAgent("test-id", "Test Agent")

@pytest.fixture
def mock_orchestrator():
    return AsyncMock()

def test_initialization(agent):
    assert agent.agent_id == "test-id"
    assert agent.name == "Test Agent"
    assert agent.orchestrator is None

def test_set_orchestrator(agent, mock_orchestrator):
    agent.set_orchestrator(mock_orchestrator)
    assert agent.orchestrator == mock_orchestrator

@pytest.mark.asyncio
async def test_send_message_with_orchestrator(agent, mock_orchestrator):
    agent.set_orchestrator(mock_orchestrator) # Set orchestrator for this test
    receiver_id = "receiver-id"
    message_type = "test-type"
    content = {"key": "value"}
    request_id = "req-123"

    await agent.send_message(receiver_id, message_type, content, request_id)

    mock_orchestrator.dispatch_message.assert_called_once()
    called_message = mock_orchestrator.dispatch_message.call_args[0][0]

    assert called_message.sender_id == agent.agent_id
    assert called_message.receiver_id == receiver_id
    assert called_message.message_type == message_type
    assert called_message.content == content
    assert called_message.request_id == request_id

@pytest.mark.asyncio
async def test_send_message_without_orchestrator(agent):
    agent.orchestrator = None # Ensure orchestrator is None
    
    # Capture print output
    with unittest.mock.patch('builtins.print') as mock_print:
        await agent.send_message("receiver-id", "test-type", {"key": "value"})
        mock_print.assert_called_once_with(f"Agent {agent.name} ({agent.agent_id}) cannot send message: Orchestrator not set.")
    agent.orchestrator.dispatch_message.assert_not_called()
