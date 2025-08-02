import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import json

from agents.queen_agent import QueenAgent
from agents.base_agent import AgentMessage, BaseAgent
from agents.sub_queen_agent import SubQueenAgent
from agents.worker_agent import WorkerAgent

@pytest.fixture
def queen_agent():
    mock_orchestrator = AsyncMock()
    agent = QueenAgent("queen-1", "Main Queen", "HIERARCHICAL")
    agent.set_orchestrator(mock_orchestrator)

    # Mock get_agents_by_type for initialization
    mock_sub_queen1 = MagicMock(spec=SubQueenAgent)
    mock_sub_queen1.agent_id = "sub-queen-1"
    mock_sub_queen1.name = "Sub Queen A"
    mock_sub_queen2 = MagicMock(spec=SubQueenAgent)
    mock_sub_queen2.agent_id = "sub-queen-2"
    mock_sub_queen2.name = "Sub Queen B"

    mock_worker1 = MagicMock(spec=WorkerAgent)
    mock_worker1.agent_id = "worker-1"
    mock_worker1.name = "Worker 1"
    mock_worker2 = MagicMock(spec=WorkerAgent)
    mock_worker2.agent_id = "worker-2"
    mock_worker2.name = "Worker 2"

    def _mock_get_agents_by_type_side_effect(agent_type):
        if agent_type is SubQueenAgent:
            return [mock_sub_queen1, mock_sub_queen2]
        elif agent_type is WorkerAgent:
            return [mock_worker1, mock_worker2]
        return []
    mock_orchestrator.get_agents_by_type.side_effect = _mock_get_agents_by_type_side_effect

    agent.initialize_agents()
    return agent, mock_orchestrator, mock_sub_queen1, mock_sub_queen2, mock_worker1, mock_worker2

@pytest.mark.asyncio
async def test_decompose_task_valid_json(queen_agent):
    agent, _, _, _, _, _ = queen_agent
    with patch('ollama.chat', new_callable=AsyncMock) as mock_ollama_chat:
        mock_ollama_chat.return_value = {"message": {"content": '["subtask1", "subtask2"]'}}
        subtasks = await agent._decompose_task("Main task")
        assert subtasks == ["subtask1", "subtask2"]

@pytest.mark.asyncio
async def test_decompose_task_invalid_json_fallback(queen_agent):
    agent, _, _, _, _, _ = queen_agent
    with patch('ollama.chat', new_callable=AsyncMock) as mock_ollama_chat:
        mock_ollama_chat.return_value = {"message": {"content": "Not a JSON string"}}
        subtasks = await agent._decompose_task("Main task")
        assert subtasks == ["Main task"]

@pytest.mark.asyncio
async def test_receive_message_task_hierarchical(queen_agent):
    agent, mock_orchestrator, mock_sub_queen1, mock_sub_queen2, _, _ = queen_agent
    agent.architecture_type = "HIERARCHICAL"
    message = AgentMessage("orchestrator", "queen-1", "task", "Complex task", "req-123")

    with patch.object(agent, '_decompose_task', new=AsyncMock(return_value=["subtask1", "subtask2"])) as mock_decompose:
        await agent.receive_message(message)

        mock_decompose.assert_called_once_with("Complex task")
        mock_orchestrator.dispatch_message.assert_has_calls([
            unittest.mock.call(AgentMessage("queen-1", "sub-queen-1", "sub-task-to-subqueen", "Delegated task from Main Queen to Sub Queen A: subtask1", "req-123")),
            unittest.mock.call(AgentMessage("queen-1", "sub-queen-2", "sub-task-to-subqueen", "Delegated task from Main Queen to Sub Queen B: subtask2", "req-123"))
        ], any_order=True)

@pytest.mark.asyncio
async def test_receive_message_task_centralized(queen_agent):
    agent, mock_orchestrator, _, _, mock_worker1, mock_worker2 = queen_agent
    agent.architecture_type = "CENTRALIZED"
    message = AgentMessage("orchestrator", "queen-1", "task", "Simple task", "req-456")

    with patch.object(agent, '_decompose_task', new=AsyncMock(return_value=["subtask_a", "subtask_b"])) as mock_decompose:
        await agent.receive_message(message)

        mock_decompose.assert_called_once_with("Simple task")
        mock_orchestrator.dispatch_message.assert_has_calls([
            unittest.mock.call(AgentMessage("queen-1", "worker-1", "sub-task", "Delegated task from Queen to Worker 1: subtask_a", "req-456")),
            unittest.mock.call(AgentMessage("queen-1", "worker-2", "sub-task", "Delegated task from Queen to Worker 2: subtask_b", "req-456"))
        ], any_order=True)

@pytest.mark.asyncio
async def test_receive_message_group_response(queen_agent):
    agent, mock_orchestrator, _, _, _, _ = queen_agent
    message = AgentMessage("sub-queen-1", "queen-1", "group-response", {"from_sub_queen": "sub-queen-1", "content": "SubQueen processed"}, "req-789")
    await agent.receive_message(message)

    mock_orchestrator.dispatch_message.assert_called_once_with(
        AgentMessage("queen-1", "orchestrator", "final-response", "Aggregated response from sub-queen-1: SubQueen processed", "req-789")
    )

@pytest.mark.asyncio
async def test_receive_message_direct_response(queen_agent):
    agent, mock_orchestrator, _, _, _, _ = queen_agent
    message = AgentMessage("worker-1", "queen-1", "response", "Worker response", "req-abc")
    await agent.receive_message(message)

    mock_orchestrator.dispatch_message.assert_called_once_with(
        AgentMessage("queen-1", "orchestrator", "final-response", "Response from worker-1: Worker response", "req-abc")
    )

@pytest.mark.asyncio
async def test_receive_message_error(queen_agent):
    agent, mock_orchestrator, _, _, _, _ = queen_agent
    message = AgentMessage("sub-queen-1", "queen-1", "error", "Error from SubQueen", "req-def")
    await agent.receive_message(message)

    mock_orchestrator.dispatch_message.assert_called_once_with(
        AgentMessage("queen-1", "orchestrator", "final-error", "Error from sub-queen-1: Error from SubQueen", "req-def")
    )