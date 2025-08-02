import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import json

from agents.sub_queen_agent import SubQueenAgent
from agents.base_agent import AgentMessage
from agents.worker_agent import WorkerAgent

@pytest.fixture
def sub_queen_agent():
    mock_orchestrator = AsyncMock()
    agent = SubQueenAgent("sub-queen-1", "Sub Queen A")
    agent.set_orchestrator(mock_orchestrator)

    mock_worker1 = MagicMock(spec=WorkerAgent)
    mock_worker1.agent_id = "worker-1"
    mock_worker1.name = "Worker 1"
    mock_worker2 = MagicMock(spec=WorkerAgent)
    mock_worker2.agent_id = "worker-2"
    mock_worker2.name = "Worker 2"

    agent.initialize_group_agents([mock_worker1, mock_worker2])
    return agent, mock_orchestrator, mock_worker1, mock_worker2

@pytest.mark.asyncio
async def test_decompose_task_valid_json(sub_queen_agent):
    agent, _, _, _ = sub_queen_agent
    with patch('ollama.chat', new_callable=AsyncMock) as mock_ollama_chat:
        mock_ollama_chat.return_value = {"message": {"content": '["subtask_worker1", "subtask_worker2"]'}}
        subtasks = await agent._decompose_task("SubQueen task")
        assert subtasks == ["subtask_worker1", "subtask_worker2"]

@pytest.mark.asyncio
async def test_decompose_task_invalid_json_fallback(sub_queen_agent):
    agent, _, _, _ = sub_queen_agent
    with patch('ollama.chat', new_callable=AsyncMock) as mock_ollama_chat:
        mock_ollama_chat.return_value = {"message": {"content": "Not a JSON string"}}
        subtasks = await agent._decompose_task("SubQueen task")
        assert subtasks == ["SubQueen task"]

@pytest.mark.asyncio
async def test_receive_message_sub_task_to_subqueen(sub_queen_agent):
    agent, mock_orchestrator, mock_worker1, mock_worker2 = sub_queen_agent
    message = AgentMessage("queen-1", "sub-queen-1", "sub-task-to-subqueen", "Task for workers", "req-123")

    with patch.object(agent, '_decompose_task', new=AsyncMock(return_value=["worker_subtask1", "worker_subtask2"])) as mock_decompose:
        await agent.receive_message(message)

        mock_decompose.assert_called_once_with("Task for workers")
        mock_orchestrator.dispatch_message.assert_has_calls([
            unittest.mock.call(AgentMessage("sub-queen-1", "worker-1", "sub-task", "Delegated by Sub Queen A to Worker 1: worker_subtask1", "req-123")),
            unittest.mock.call(AgentMessage("sub-queen-1", "worker-2", "sub-task", "Delegated by Sub Queen A to Worker 2: worker_subtask2", "req-123"))
        ], any_order=True)

@pytest.mark.asyncio
async def test_receive_message_response_from_worker(sub_queen_agent):
    agent, mock_orchestrator, _, _ = sub_queen_agent
    message = AgentMessage("worker-1", "sub-queen-1", "response", "Worker response", "req-456")
    await agent.receive_message(message)

    mock_orchestrator.dispatch_message.assert_called_once_with(
        AgentMessage("sub-queen-1", "queen-agent-1", "group-response", {
            "from_sub_queen": "sub-queen-1",
            "original_sender": "worker-1",
            "type": "response",
            "content": "Worker response",
        }, "req-456")
    )

@pytest.mark.asyncio
async def test_receive_message_error_from_worker(sub_queen_agent):
    agent, mock_orchestrator, _, _ = sub_queen_agent
    message = AgentMessage("worker-1", "sub-queen-1", "error", "Worker error", "req-789")
    await agent.receive_message(message)

    mock_orchestrator.dispatch_message.assert_called_once_with(
        AgentMessage("sub-queen-1", "queen-agent-1", "group-response", {
            "from_sub_queen": "sub-queen-1",
            "original_sender": "worker-1",
            "type": "error",
            "content": "Worker error",
        }, "req-789")
    )
