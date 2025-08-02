import asyncio
import os
from dotenv import load_dotenv

from orchestrator.orchestrator import Orchestrator
from agents.queen_agent import QueenAgent
from agents.sub_queen_agent import SubQueenAgent
from agents.worker_agent import WorkerAgent

load_dotenv()

async def main():
    orchestrator = Orchestrator()

    # Configuration from environment variables or defaults
    worker_count = int(os.getenv("OLLAMA_WORKER_COUNT", "4"))
    architecture_type = os.getenv("OLLAMA_ARCHITECTURE_TYPE", "HIERARCHICAL")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
    project_folder = os.getenv("OLLAMA_PROJECT_FOLDER")

    # Register Queen Agent
    queen_agent = QueenAgent("queen-agent-1", "Main Queen", architecture_type, ollama_model)
    orchestrator.register_agent(queen_agent)

    # Register Worker Agents and Sub-Queen Agents based on architecture
    if architecture_type == "HIERARCHICAL":
        sub_queen_count = int(os.getenv("OLLAMA_SUB_QUEEN_COUNT", "2"))
        sub_queen_groups = [[] for _ in range(sub_queen_count)]

        worker_agents = []
        for i in range(worker_count):
            worker = WorkerAgent(f"worker-agent-{i+1}", f"Worker {i+1}", ollama_model, project_folder)
            worker_agents.append(worker)
            orchestrator.register_agent(worker)
            sub_queen_groups[i % sub_queen_count].append(worker) # Distribute workers among sub-queens

        sub_queen_agents = []
        for i in range(sub_queen_count):
            sub_queen = SubQueenAgent(f"sub-queen-{i+1}", f"Sub Queen {chr(65+i)}", ollama_model)
            sub_queen.initialize_group_agents(sub_queen_groups[i])
            orchestrator.register_agent(sub_queen)
            sub_queen_agents.append(sub_queen)

    elif architecture_type in ["CENTRALIZED", "FULLY_CONNECTED"]:
        # For these architectures, workers are directly managed by the Queen
        for i in range(worker_count):
            worker = WorkerAgent(f"worker-agent-{i+1}", f"Worker {i+1}", ollama_model, project_folder)
            orchestrator.register_agent(worker)

    # Initialize Queen Agent after all other agents are registered
    queen_agent.initialize_agents()

    print("Ollama Flow Framework initialized.")
    print(f"Architecture: {architecture_type}, Workers: {worker_count}, Model: {ollama_model}")
    if project_folder:
        print(f"Project Folder: {project_folder}")

    # Example usage: Send a prompt to the Queen Agent
    prompt = "Please write a simple Python Flask app that says 'Hello, World!' and save it to app.py in the project folder."
    # prompt = "execute command: ls -la"
    # prompt = "Please tell me about the capital of France."

    response = await orchestrator.run(prompt)
    print(f"\nFinal Response from Orchestrator: {response}")

if __name__ == "__main__":
    asyncio.run(main())
