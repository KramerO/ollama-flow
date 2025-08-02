import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from orchestrator.orchestrator import Orchestrator
from agents.base_agent import BaseAgent, AgentMessage

class MockAgent(BaseAgent):
    def __init__(self, agent_id: str, name: str):
        super().__init__(agent_id, name)
        self.received_messages = []

    async def receive_message(self, message: AgentMessage):
        self.received_messages.append(message)

@pytest.fixture
def orchestrator():
    orchestrator_instance = Orchestrator()
    mock_agent1 = MockAgent("agent1", "Agent One")
    mock_agent2 = MockAgent("agent2", "Agent Two")
    orchestrator_instance.register_agent(mock_agent1)
    orchestrator_instance.register_agent(mock_agent2)
    return orchestrator_instance, mock_agent1, mock_agent2

def test_register_agent(orchestrator):
    orchestrator_instance, mock_agent1, _ = orchestrator
    assert "agent1" in orchestrator_instance.agents
    assert orchestrator_instance.agents["agent1"] == mock_agent1
    assert mock_agent1.orchestrator == orchestrator_instance

@pytest.mark.asyncio
async def test_dispatch_message_to_agent(orchestrator):
    orchestrator_instance, mock_agent1, _ = orchestrator
    message = AgentMessage("sender", "agent1", "test", "Hello Agent1")
    await orchestrator_instance.dispatch_message(message)
    assert len(mock_agent1.received_messages) == 1
    assert mock_agent1.received_messages[0].content == "Hello Agent1"

@pytest.mark.asyncio
async def test_dispatch_message_unknown_receiver(orchestrator):
    orchestrator_instance, _, _ = orchestrator
    message = AgentMessage("sender", "unknown_agent", "test", "Hello Unknown")
    with unittest.mock.patch('builtins.print') as mock_print:
        await orchestrator_instance.dispatch_message(message)
        mock_print.assert_called_once_with("Error: Agent with ID unknown_agent not found.")

@pytest.mark.asyncio
async def test_dispatch_message_final_response(orchestrator):
    orchestrator_instance, _, _ = orchestrator
    future = asyncio.Future()
    orchestrator_instance.response_resolvers["req-123"] = future

    message = AgentMessage("agent1", "orchestrator", "final-response", "Final Answer", "req-123")
    await orchestrator_instance.dispatch_message(message)

    assert future.done()
    assert await future == "Final Answer"
    assert "req-123" not in orchestrator_instance.response_resolvers

@pytest.mark.asyncio
async def test_dispatch_message_final_error(orchestrator):
    orchestrator_instance, _, _ = orchestrator
    future = asyncio.Future()
    orchestrator_instance.response_resolvers["req-123"] = future

    message = AgentMessage("agent1", "orchestrator", "final-error", "Error occurred", "req-123")
    await orchestrator_instance.dispatch_message(message)

    assert future.done()
    with pytest.raises(Exception, match="Error occurred"):
        await future
    assert "req-123" not in orchestrator_instance.response_resolvers

@pytest.mark.asyncio
async def test_run_method(orchestrator):
    orchestrator_instance, _, _ = orchestrator
    # Mock the QueenAgent to control its behavior
    mock_queen_agent = AsyncMock(spec=BaseAgent)
    mock_queen_agent.agent_id = "queen-agent-1"
    mock_queen_agent.name = "Mock Queen"
    orchestrator_instance.register_agent(mock_queen_agent)

    # Mock the _decompose_task method of the QueenAgent
    mock_queen_agent._decompose_task = AsyncMock(return_value=["subtask1", "subtask2"])

    # Mock the send_message method of the QueenAgent to resolve the orchestrator's future
    async def mock_send_message(receiver_id, message_type, content, request_id):
        if receiver_id == "orchestrator" and message_type == "final-response":
            orchestrator_instance.response_resolvers[request_id].set_result(content)

    mock_queen_agent.send_message.side_effect = mock_send_message

    # Run the orchestrator with a prompt
    prompt = "Initial task for Queen"
    
    final_response = await orchestrator_instance.run(prompt)

    assert final_response == "Aggregated response from None: Mocked Ollama Response" # Adjust based on actual QueenAgent response
    mock_queen_agent.receive_message.assert_called_once()
    assert mock_queen_agent.receive_message.call_args[0][0].content == prompt

def test_get_agents_by_type(orchestrator):
    orchestrator_instance, mock_agent1, mock_agent2 = orchestrator
    mock_worker_agent = MockAgent("worker1", "Worker One")
    orchestrator_instance.register_agent(mock_worker_agent)

    # Assuming MockAgent is a BaseAgent for this test
    base_agents = orchestrator_instance.get_agents_by_type(BaseAgent)
    assert mock_agent1 in base_agents
    assert mock_agent2 in base_agents
    assert mock_worker_agent in base_agents
