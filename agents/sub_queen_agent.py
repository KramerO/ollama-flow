import ollama
import asyncio
import json
from typing import List, Type, Optional

from agents.base_agent import BaseAgent, AgentMessage
from agents.drone_agent import DroneAgent, DroneRole
from agents.secure_drone_agent import SecureDroneAgent
from typing import Dict

class SubQueenAgent(BaseAgent):
    def __init__(self, agent_id: str, name: str, model: str = "llama3"):
        super().__init__(agent_id, name)
        self.model = model
        self.group_drone_agents: List[DroneAgent] = []
        self.drone_roles: Dict[str, DroneRole] = {}  # agent_id -> role mapping
        self.current_agent_index = 0

    def initialize_group_agents(self, agents: List[DroneAgent]):
        self.group_drone_agents = agents
        self._initialize_drone_roles()
        print(f"SubQueenAgent {self.name} initialized with {len(self.group_drone_agents)} DroneAgents.")

    async def _decompose_task(self, task: str) -> List[str]:
        decomposition_prompt = f"Given the sub-task: '{task}'. Decompose this into a list of smaller, actionable subtasks for specialized drone agents. Consider different roles like analyst, data scientist, IT architect, and developer. Respond only with a JSON array of strings, where each string is a subtask. Example: ['Subtask 1', 'Subtask 2']"
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": decomposition_prompt}],
            )
            raw_response = response["message"]["content"]
            print(f"[SubQueenAgent] Decomposition LLM Raw Response: {raw_response}")
            try:
                # Clean the response - remove markdown code blocks
                cleaned_response = raw_response.strip()
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]  # Remove ```json
                if cleaned_response.startswith('```'):
                    cleaned_response = cleaned_response[3:]   # Remove ```
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]  # Remove trailing ```
                cleaned_response = cleaned_response.strip()
                
                # Fix Windows path separators and other escape sequences
                import re
                # More comprehensive Windows path fixing
                # Replace D:\path\to\file with D:/path/to/file in JSON strings
                cleaned_response = re.sub(r'([A-Z]):\\+([^"\\]*\\[^"\\]*)', lambda m: f'{m.group(1)}:/{m.group(2).replace(chr(92), "/")}', cleaned_response)
                # Fix remaining Windows paths
                cleaned_response = re.sub(r'([A-Z]):\\([^"]*)', r'\1:/\2', cleaned_response)
                # Replace any remaining single backslashes with forward slashes in paths
                cleaned_response = re.sub(r'([A-Z]:)/([^"]*?)\\([^"]*)', r'\1/\2/\3', cleaned_response)
                # Escape remaining backslashes that aren't valid JSON escapes
                cleaned_response = re.sub(r'\\(?!["\\bfnrt/uU0-9a-fA-F])', r'\\\\', cleaned_response)
                
                subtasks = json.loads(cleaned_response)
                if isinstance(subtasks, list) and all(isinstance(item, str) for item in subtasks):
                    return subtasks
                else:
                    print(f"[SubQueenAgent] LLM response is not a valid JSON array of strings. Falling back to single task.")
                    print(f"[SubQueenAgent] Cleaned response was: {cleaned_response[:200]}...")
                    return [task]
            except json.JSONDecodeError as e:
                print(f"[SubQueenAgent] JSON parsing failed: {e}. Falling back to single task.")
                print(f"[SubQueenAgent] Raw response: {raw_response[:500]}...")
                print(f"[SubQueenAgent] Cleaned response: {cleaned_response[:500]}...")
                print(f"[SubQueenAgent] Error location: line {getattr(e, 'lineno', 'unknown')}, column {getattr(e, 'colno', 'unknown')}")
                return [task]
        except Exception as e:
            print(f"[SubQueenAgent] Error during task decomposition: {e}. Falling back to single task.")
            return [task]

    async def receive_message(self, message: AgentMessage):
        print(f"SubQueenAgent {self.name} ({self.agent_id}) received message from {message.sender_id}: {message.content}")

        if message.message_type == "sub-task-to-subqueen":
            subtasks = await self._decompose_task(message.content)
            print(f"[SubQueenAgent] Decomposed into subtasks: {subtasks}")

            for subtask in subtasks:
                if not self.group_drone_agents:
                    print(f"SubQueenAgent {self.name}: No DroneAgents in group to delegate tasks.")
                    await self.send_message(message.sender_id, "error", f"No DroneAgents in group for {self.name}", message.request_id)
                    return

                # Determine optimal role for subtask and assign appropriate drone
                optimal_role = self._determine_task_role(subtask)
                target_drone = self._get_drone_for_role(optimal_role)
                
                if not target_drone:
                    # Fallback to round-robin if no role match found
                    target_drone = self.group_drone_agents[self.current_agent_index]
                    self.current_agent_index = (self.current_agent_index + 1) % len(self.group_drone_agents)
                
                # Update drone role if it supports it
                if hasattr(target_drone, 'role'):
                    target_drone.role = optimal_role
                    if hasattr(target_drone, '_get_role_capabilities'):
                        target_drone.capabilities = target_drone._get_role_capabilities()
                
                self.drone_roles[target_drone.agent_id] = optimal_role

                delegated_task = self._structure_task_for_drone(subtask, optimal_role, target_drone.name)
                print(f"SubQueenAgent {self.name} delegating {optimal_role.value} task to {target_drone.name} ({target_drone.agent_id}) - Original drone role: {getattr(target_drone, 'role', 'unknown')}")
                await self.send_message(target_drone.agent_id, "sub-task", delegated_task, message.request_id)

        elif message.message_type == "response" or message.message_type == "error":
            print(f"SubQueenAgent {self.name} received {message.message_type} from {message.sender_id}: {message.content}")
            await self.send_message("queen-agent-1", "group-response", {
                "from_sub_queen": self.agent_id,
                "original_sender": message.sender_id,
                "type": message.message_type,
                "content": message.content,
            }, message.request_id)
            
    def _initialize_drone_roles(self):
        """Initialize drone roles for available drones"""
        available_roles = list(DroneRole)
        for i, drone in enumerate(self.group_drone_agents):
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
                'statistics', 'correlation', 'regression', 'classification',
                'opencv', 'cv2', 'image recognition', 'computer vision', 'bildverarbeitung',
                'bilderkennungs', 'bilderkennung', 'image processing', 'drone perspective',
                'pattern recognition', 'feature detection', 'object detection'
            ],
            DroneRole.ANALYST: [
                'analyze', 'report', 'document', 'review', 'assess', 'evaluate',
                'metrics', 'dashboard', 'visualization', 'chart', 'graph',
                'insights', 'trends', 'patterns', 'summary', 'daten', 'data'
            ],
            DroneRole.IT_ARCHITECT: [
                'architecture', 'design', 'system', 'infrastructure', 'scalability',
                'microservices', 'api', 'database', 'security', 'deployment',
                'cloud', 'docker', 'kubernetes', 'projekt', 'project structure'
            ],
            DroneRole.DEVELOPER: [
                'code', 'develop', 'implement', 'build', 'create', 'program',
                'function', 'class', 'script', 'application', 'web', 'frontend',
                'backend', 'debug', 'test', 'fix', 'python', 'erstelle', 'baust'
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
        
    def _get_drone_for_role(self, role: DroneRole) -> Optional[DroneAgent]:
        """Get a drone that matches the specified role"""
        # First try to find a drone already assigned to this role
        for drone in self.group_drone_agents:
            if self.drone_roles.get(drone.agent_id) == role:
                return drone
                
        # If no exact match, return first available drone
        return self.group_drone_agents[0] if self.group_drone_agents else None
        
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
=== SUB-QUEEN ROLE-BASED TASK ASSIGNMENT ===
SubQueen: {self.name}
Drone: {drone_name}
Role: {role.value.upper()}
Context: {context}

Task: {task}

=== EXECUTION GUIDELINES ===
1. Approach this task from your assigned role perspective
2. Use role-specific methodologies and best practices
3. Consider task dependencies and prerequisites
4. Coordinate with other drones if needed
5. Report completion status to SubQueen

=== TASK DEPENDENCIES ===
Ensure proper execution order:
1. Analyze requirements
2. Check prerequisites
3. Execute main task
4. Validate results
5. Report back
"""
        
        return structured_task
