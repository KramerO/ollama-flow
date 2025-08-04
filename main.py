import asyncio
import os
import argparse
from dotenv import load_dotenv

from orchestrator.orchestrator import Orchestrator
from agents.queen_agent import QueenAgent
from agents.sub_queen_agent import SubQueenAgent
from agents.drone_agent import DroneAgent, DroneRole
from db_manager import MessageDBManager # Import the new DB Manager

load_dotenv()

async def main():
    parser = argparse.ArgumentParser(description="Ollama Flow Framework CLI")
    parser.add_argument("--task", type=str, help="The task prompt for the orchestrator.")
    parser.add_argument("--project-folder", type=str, help="The project folder path.")
    parser.add_argument("--drone-count", type=int, help="Number of drone agents.")
    parser.add_argument("--worker-count", type=int, help="Number of drone agents (legacy, use --drone-count).")  # Legacy support
    parser.add_argument("--architecture-type", type=str, choices=["HIERARCHICAL", "CENTRALIZED", "FULLY_CONNECTED"], help="Architecture type (HIERARCHICAL, CENTRALIZED, FULLY_CONNECTED).")
    parser.add_argument("--ollama-model", type=str, help="Ollama model to use (e.g., llama3).")
    args = parser.parse_args()

    # Initialize DB Manager
    db_manager = MessageDBManager(db_path='ollama_flow_messages.db')

    try:
        orchestrator = Orchestrator(db_manager)

        # Determine drone_count (with legacy worker_count support)
        drone_count_from_env = os.getenv("OLLAMA_DRONE_COUNT") or os.getenv("OLLAMA_WORKER_COUNT")
        if args.drone_count is not None:
            worker_count = args.drone_count
        elif args.worker_count is not None:  # Legacy support
            worker_count = args.worker_count
        elif drone_count_from_env is not None:
            worker_count = int(drone_count_from_env)
        else:
            while True:
                try:
                    dc_input = input("Enter number of drone agents (default: 4): ").strip()
                    worker_count = int(dc_input) if dc_input else 4
                    break
                except ValueError:
                    print("Invalid input. Please enter a number.")

        # Determine architecture_type
        architecture_type_from_env = os.getenv("OLLAMA_ARCHITECTURE_TYPE")
        if args.architecture_type is not None:
            architecture_type = args.architecture_type
        elif architecture_type_from_env is not None:
            architecture_type = architecture_type_from_env
        else:
            while True:
                at_input = input("Enter architecture type (HIERARCHICAL, CENTRALIZED, FULLY_CONNECTED) (default: HIERARCHICAL): ").strip().upper()
                if at_input in ["HIERARCHICAL", "CENTRALIZED", "FULLY_CONNECTED"]:
                    architecture_type = at_input
                    break
                elif not at_input:
                    architecture_type = "HIERARCHICAL"
                    break
                else:
                    print("Invalid input. Please choose from HIERARCHICAL, CENTRALIZED, or FULLY_CONNECTED.")

        # Determine ollama_model
        ollama_model_from_env = os.getenv("OLLAMA_MODEL")
        if args.ollama_model is not None:
            ollama_model = args.ollama_model
        elif ollama_model_from_env is not None:
            ollama_model = ollama_model_from_env
        else:
            om_input = input("Enter Ollama model to use (default: llama3): ").strip()
            ollama_model = om_input if om_input else "llama3"

        # Determine project_folder
        project_folder = args.project_folder or os.getenv("OLLAMA_PROJECT_FOLDER")
        if not project_folder:
            project_folder = input("Enter the project folder path (e.g., /tmp/my_project) (default: current directory): ").strip()
            if not project_folder:
                project_folder = os.getcwd()

        # Determine prompt (task)
        prompt = args.task
        if not prompt:
            prompt = input("Enter the task prompt: ").strip()
            if not prompt:
                print("No task prompt provided. Exiting.")
                return

        # Register Queen Agent
        queen_agent = QueenAgent("queen-agent-1", "Main Queen", architecture_type, ollama_model)
        orchestrator.register_agent(queen_agent)

        # Register Worker Agents and Sub-Queen Agents based on architecture
        if architecture_type == "HIERARCHICAL":
            sub_queen_count = int(os.getenv("OLLAMA_SUB_QUEEN_COUNT", "2"))
            sub_queen_groups = [[] for _ in range(sub_queen_count)]

            worker_agents = []
            for i in range(worker_count):
                # Assign roles in round-robin fashion
                available_roles = list(DroneRole)
                role = available_roles[i % len(available_roles)]
                drone = DroneAgent(f"drone-agent-{i+1}", f"Drone {i+1} ({role.value})", ollama_model, project_folder, role)
                worker_agents.append(drone)
                orchestrator.register_agent(drone)
                sub_queen_groups[i % sub_queen_count].append(drone) # Distribute drones among sub-queens
                print(f"Created drone agent {i+1} with role: {role.value}")

            sub_queen_agents = []
            for i in range(sub_queen_count):
                sub_queen = SubQueenAgent(f"sub-queen-{i+1}", f"Sub Queen {chr(65+i)}", ollama_model)
                sub_queen.initialize_group_agents(sub_queen_groups[i])
                orchestrator.register_agent(sub_queen)
                sub_queen_agents.append(sub_queen)

        elif architecture_type in ["CENTRALIZED", "FULLY_CONNECTED"]:
            # For these architectures, workers are directly managed by the Queen
            for i in range(worker_count):
                # Assign roles in round-robin fashion
                available_roles = list(DroneRole)
                role = available_roles[i % len(available_roles)]
                drone = DroneAgent(f"drone-agent-{i+1}", f"Drone {i+1} ({role.value})", ollama_model, project_folder, role)
                orchestrator.register_agent(drone)
                print(f"Created drone agent {i+1} with role: {role.value}")

        # Initialize Queen Agent after all other agents are registered
        queen_agent.initialize_agents()

        # Start orchestrator polling
        orchestrator.start_polling()

        print("Ollama Flow Framework initialized.")
        print(f"Architecture: {architecture_type}, Workers: {worker_count}, Model: {ollama_model}")
        if project_folder:
            print(f"Project Folder: {project_folder}")

        response = await orchestrator.run(prompt)
        print(f"\nFinal Response from Orchestrator: {response}")

    finally:
        db_manager.close()
        print("Database connection closed.")

if __name__ == "__main__":
    asyncio.run(main())