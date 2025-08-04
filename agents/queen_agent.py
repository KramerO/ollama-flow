import ollama
import asyncio
import json
from typing import List, Type, Optional

from agents.base_agent import BaseAgent, AgentMessage
from agents.sub_queen_agent import SubQueenAgent
from agents.drone_agent import DroneAgent, DroneRole
from agents.secure_drone_agent import SecureDroneAgent
from typing import Dict, Tuple

class QueenAgent(BaseAgent):
    def __init__(self, agent_id: str, name: str, architecture_type: str, model: str = "llama3"):
        super().__init__(agent_id, name)
        self.architecture_type = architecture_type
        self.model = model
        self.sub_queen_agents: List[BaseAgent] = []
        self.drone_agents: List[BaseAgent] = []
        self.drone_roles: Dict[str, DroneRole] = {}  # agent_id -> role mapping
        self.current_sub_queen_index = 0
        self.current_drone_index = 0

    def initialize_agents(self):
        if self.orchestrator:
            if self.architecture_type == 'HIERARCHICAL':
                self.sub_queen_agents = self.orchestrator.get_agents_by_type(SubQueenAgent)
                print(f"QueenAgent {self.name} found {len(self.sub_queen_agents)} SubQueenAgents.")
            elif self.architecture_type in ['CENTRALIZED', 'FULLY_CONNECTED']:
                # Try SecureDroneAgent first, fallback to DroneAgent
                self.drone_agents = self.orchestrator.get_agents_by_type(SecureDroneAgent)
                if not self.drone_agents:
                    self.drone_agents = self.orchestrator.get_agents_by_type(DroneAgent)
                print(f"QueenAgent {self.name} found {len(self.drone_agents)} DroneAgents.")
                self._initialize_drone_roles()

    async def _decompose_task(self, task: str) -> List[str]:
        decomposition_prompt = f"Given the main task: '{task}'. Decompose this into a list of smaller, actionable subtasks. Respond only with a JSON array of strings, where each string is a subtask. Example: ['Subtask 1', 'Subtask 2']"
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": decomposition_prompt}],
            )
            raw_response = response["message"]["content"]
            print(f"[QueenAgent] Decomposition LLM Raw Response: {raw_response}")
            try:
                subtasks = json.loads(raw_response)
                if isinstance(subtasks, list) and all(isinstance(item, str) for item in subtasks):
                    return subtasks
                else:
                    print(f"[QueenAgent] LLM response is not a valid JSON array of strings. Falling back to single task.")
                    return [task]
            except json.JSONDecodeError as e:
                print(f"[QueenAgent] JSON parsing failed: {e}. Falling back to single task.")
                return [task]
        except Exception as e:
            print(f"[QueenAgent] Error during task decomposition: {e}. Falling back to single task.")
            return [task]

    def _initialize_drone_roles(self):
        """Initialize drone roles for available drones"""
        available_roles = list(DroneRole)
        for i, drone in enumerate(self.drone_agents):
            # Assign roles in round-robin fashion initially
            role = available_roles[i % len(available_roles)]
            self.drone_roles[drone.agent_id] = role
            
            # Update drone role if it supports it
            if hasattr(drone, 'role'):
                drone.role = role
                if hasattr(drone, '_get_role_capabilities'):
                    drone.capabilities = drone._get_role_capabilities()
                    
    def _determine_task_role(self, task: str) -> DroneRole:
        """Determine the most appropriate role for a given task"""
        task_lower = task.lower()
        
        # Keywords that suggest specific roles
        role_keywords = {
            DroneRole.DATA_SCIENTIST: [
                'machine learning', 'ml', 'model', 'train', 'predict', 'dataset',
                'pandas', 'numpy', 'scikit', 'tensorflow', 'pytorch', 'analysis',
                'statistics', 'correlation', 'regression', 'classification'
            ],
            DroneRole.ANALYST: [
                'analyze', 'report', 'document', 'review', 'assess', 'evaluate',
                'metrics', 'dashboard', 'visualization', 'chart', 'graph',
                'insights', 'trends', 'patterns', 'summary'
            ],
            DroneRole.IT_ARCHITECT: [
                'architecture', 'design', 'system', 'infrastructure', 'scalability',
                'microservices', 'api', 'database', 'security', 'deployment',
                'cloud', 'docker', 'kubernetes', 'architecture'
            ],
            DroneRole.DEVELOPER: [
                'code', 'develop', 'implement', 'build', 'create', 'program',
                'function', 'class', 'script', 'application', 'web', 'frontend',
                'backend', 'debug', 'test', 'fix'
            ]
        }
        
        # Score each role based on keyword matches
        role_scores = {}
        for role, keywords in role_keywords.items():
            score = sum(1 for keyword in keywords if keyword in task_lower)
            role_scores[role] = score
            
        # Return role with highest score, default to DEVELOPER
        best_role = max(role_scores.items(), key=lambda x: x[1])
        return best_role[0] if best_role[1] > 0 else DroneRole.DEVELOPER
        
    def _assign_optimal_drone_for_task(self, task: str) -> Tuple[BaseAgent, DroneRole]:
        """Assign the most suitable drone for a task based on role matching"""
        required_role = self._determine_task_role(task)
        
        # Look for drones already assigned to this role
        for drone in self.drone_agents:
            if self.drone_roles.get(drone.agent_id) == required_role:
                return drone, required_role
                
        # If no exact match, find the best available drone
        if self.drone_agents:
            return self.drone_agents[0], required_role
            
        return None, required_role
        
    def _structure_task_for_drone(self, task: str, role: DroneRole, drone_name: str) -> str:
        """Structure task with role-specific context and dependencies"""
        role_context = {
            DroneRole.ANALYST: "As an analyst drone, focus on data analysis, pattern recognition, and generating comprehensive reports.",
            DroneRole.DATA_SCIENTIST: "As a data scientist drone, focus on machine learning, statistical analysis, and data-driven insights.",
            DroneRole.IT_ARCHITECT: "As an IT architect drone, focus on system design, scalability, security, and infrastructure planning.",
            DroneRole.DEVELOPER: "As a developer drone, focus on coding, implementation, testing, and creating functional solutions."
        }
        
        context = role_context.get(role, "Complete the assigned task efficiently.")
        
        structured_task = f"""
=== ROLE-BASED TASK ASSIGNMENT ===
Drone: {drone_name}
Role: {role.value.upper()}
Context: {context}

Task: {task}

=== EXECUTION GUIDELINES ===
1. Approach this task from your role perspective
2. Use role-specific best practices and methodologies
3. Consider dependencies and prerequisites
4. Provide clear documentation of your work
5. Report any issues or blockers immediately

=== TASK DEPENDENCIES ===
Ensure the following order if multiple operations are needed:
1. Check prerequisites (files, directories, dependencies)
2. Create required structure if missing
3. Execute main task
4. Validate results
5. Document completion
"""
        
        return structured_task
        
    def _detect_task_dependencies(self, task: str) -> List[str]:
        """Detect potential dependencies in a task"""
        dependencies = []
        task_lower = task.lower()
        
        # Common dependency patterns
        if 'file' in task_lower and 'directory' in task_lower:
            dependencies.append("Ensure target directory exists before creating files")
        if 'install' in task_lower and 'package' in task_lower:
            dependencies.append("Check package manager availability")
        if 'database' in task_lower:
            dependencies.append("Verify database connection and permissions")
        if 'api' in task_lower:
            dependencies.append("Ensure network connectivity and API availability")
            
        return dependencies

    async def receive_message(self, message: AgentMessage):
        print(f"QueenAgent {self.name} ({self.agent_id}) received message from {message.sender_id}: {message.content}")

        if message.message_type == "task":
            subtasks = await self._decompose_task(message.content)
            print(f"[QueenAgent] Decomposed into subtasks: {subtasks}")

            for subtask in subtasks:
                if self.architecture_type == 'HIERARCHICAL':
                    if not self.sub_queen_agents:
                        print("No SubQueenAgents available to delegate tasks.")
                        await self.send_message("orchestrator", "final-error", "No SubQueenAgents available.", message.request_id)
                        return

                    target_sub_queen = self.sub_queen_agents[self.current_sub_queen_index]
                    self.current_sub_queen_index = (self.current_sub_queen_index + 1) % len(self.sub_queen_agents)

                    delegated_task = f"Delegated task from Main Queen to {target_sub_queen.name}: {subtask}"
                    print(f"QueenAgent delegating task to {target_sub_queen.name} ({target_sub_queen.agent_id})")
                    await self.send_message(target_sub_queen.agent_id, "sub-task-to-subqueen", delegated_task, message.request_id)
                elif self.architecture_type in ['CENTRALIZED', 'FULLY_CONNECTED']:
                    if not self.drone_agents:
                        print("No DroneAgents available to delegate tasks.")
                        await self.send_message("orchestrator", "final-error", "No DroneAgents available.", message.request_id)
                        return

                    # Assign role and select appropriate drone
                    optimal_drone, assigned_role = self._assign_optimal_drone_for_task(subtask)
                    
                    if not optimal_drone:
                        # Fallback to round-robin if no optimal match
                        optimal_drone = self.drone_agents[self.current_drone_index]
                        self.current_drone_index = (self.current_drone_index + 1) % len(self.drone_agents)
                        assigned_role = self._determine_task_role(subtask)
                    
                    # Update drone role if it has role assignment capability
                    if hasattr(optimal_drone, 'role'):
                        optimal_drone.role = assigned_role
                        if hasattr(optimal_drone, '_get_role_capabilities'):
                            optimal_drone.capabilities = optimal_drone._get_role_capabilities()
                    
                    self.drone_roles[optimal_drone.agent_id] = assigned_role

                    delegated_task = self._structure_task_for_drone(subtask, assigned_role, optimal_drone.name)
                    print(f"QueenAgent delegating {assigned_role.value} task to {optimal_drone.name} ({optimal_drone.agent_id})")
                    await self.send_message(optimal_drone.agent_id, "sub-task", delegated_task, message.request_id)

        elif message.message_type == "group-response":
            print(f"QueenAgent received group response from {message.sender_id}: {message.content}")
            await self.send_message("orchestrator", "final-response", f"Aggregated response from {message.content['from_sub_queen']}: {message.content['content']}", message.request_id)
        elif message.message_type == "response":
            print(f"QueenAgent received direct response from {message.sender_id}: {message.content}")
            await self.send_message("orchestrator", "final-response", f"Response from {message.sender_id}: {message.content}", message.request_id)
        elif message.message_type == "error":
            print(f"QueenAgent received error from {message.sender_id}: {message.content}")
            await self.send_message("orchestrator", "final-error", f"Error from {message.sender_id}: {message.content}", message.request_id)
