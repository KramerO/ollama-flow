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
                # Try multiple parsing strategies
                subtasks = self._parse_subtasks_robust(raw_response)
                if subtasks:
                    return subtasks
                else:
                    print(f"[QueenAgent] All parsing strategies failed. Falling back to single task.")
                    return [task]
            except json.JSONDecodeError as e:
                print(f"[QueenAgent] JSON parsing failed: {e}. Falling back to single task.")
                print(f"[QueenAgent] Raw response: {raw_response[:500]}...")
                print(f"[QueenAgent] Cleaned response: {cleaned_response[:500]}...")
                print(f"[QueenAgent] Error location: line {getattr(e, 'lineno', 'unknown')}, column {getattr(e, 'colno', 'unknown')}")
                return [task]
        except Exception as e:
            print(f"[QueenAgent] Error during task decomposition: {e}. Falling back to single task.")
            return [task]

    def _parse_subtasks_robust(self, raw_response: str) -> list:
        """Try multiple strategies to parse subtasks from LLM response"""
        import re
        
        # Strategy 1: Standard JSON parsing with cleanup
        try:
            cleaned_response = raw_response.strip()
            # Remove markdown code blocks
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            # Fix common JSON issues
            # Fix unescaped quotes in strings
            cleaned_response = re.sub(r'`print\("([^"]*)"[)]`', r'print(\1)', cleaned_response)
            cleaned_response = re.sub(r'"([^"]*)`([^"`]*)`([^"]*)"', r'"\1\2\3"', cleaned_response)
            
            # Try to parse
            subtasks = json.loads(cleaned_response)
            if isinstance(subtasks, list) and all(isinstance(item, str) for item in subtasks):
                print(f"[QueenAgent] Strategy 1 successful: {len(subtasks)} subtasks")
                return subtasks
        except:
            pass
        
        # Strategy 2: Extract array items with regex
        try:
            array_pattern = r'\[([^\[\]]*(?:"[^"]*"[^[\]]*)*)\]'
            match = re.search(array_pattern, raw_response, re.DOTALL)
            if match:
                array_content = match.group(1)
                # Simple item extraction
                items = []
                # Find quoted strings
                item_pattern = r'"([^"]*(?:\\.[^"]*)*)"'
                for item_match in re.finditer(item_pattern, array_content):
                    items.append(item_match.group(1))
                
                if items:
                    print(f"[QueenAgent] Strategy 2 successful: {len(items)} subtasks")
                    return items
        except:
            pass
            
        # Strategy 3: Line-by-line extraction
        try:
            lines = raw_response.split('\n')
            subtasks = []
            for line in lines:
                line = line.strip()
                # Look for quoted strings or numbered items
                if line.startswith('"') and line.endswith('",'):
                    subtasks.append(line[1:-2])  # Remove quotes and comma
                elif line.startswith('"') and line.endswith('"'):
                    subtasks.append(line[1:-1])  # Remove quotes
                elif re.match(r'^\d+\.\s*(.+)', line):
                    # Numbered list item
                    subtasks.append(re.match(r'^\d+\.\s*(.+)', line).group(1))
            
            if subtasks:
                print(f"[QueenAgent] Strategy 3 successful: {len(subtasks)} subtasks")
                return subtasks
        except:
            pass
            
        print("[QueenAgent] All parsing strategies failed")
        return None

    def _initialize_drone_roles(self):
        """Initialize drone roles for available drones (no pre-assignment for dynamic role system)"""
        print(f"[QueenAgent] {len(self.drone_agents)} drones initialized with dynamic role assignment capability")
                    
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
            ],
            DroneRole.SECURITY_SPECIALIST: [
                'security', 'secure', 'vulnerability', 'audit', 'penetration', 'encrypt',
                'authenticate', 'authorize', 'compliance', 'threat', 'attack', 'defense',
                'owasp', 'csrf', 'xss', 'injection', 'authentication', 'authorization',
                'ssl', 'tls', 'firewall', 'intrusion', 'malware', 'breach', 'privacy',
                'sicherheit', 'verschlüsselung', 'angriff', 'schutz', 'bedrohung'
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
            DroneRole.DEVELOPER: "As a developer drone, focus on coding, implementation, testing, and creating functional solutions.",
            DroneRole.SECURITY_SPECIALIST: "As a security specialist drone, focus on identifying vulnerabilities, implementing secure coding practices, conducting security audits, and ensuring compliance with security standards."
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

                    # Use round-robin to select drone (role will be assigned dynamically by the drone)
                    optimal_drone = self.drone_agents[self.current_drone_index]
                    self.current_drone_index = (self.current_drone_index + 1) % len(self.drone_agents)

                    # Send task directly - drone will assign its own role dynamically
                    print(f"QueenAgent delegating task to {optimal_drone.name} ({optimal_drone.agent_id}) for dynamic role assignment")
                    await self.send_message(optimal_drone.agent_id, "sub-task", subtask, message.request_id)

        elif message.message_type == "group-response":
            print(f"QueenAgent received group response from {message.sender_id}: {message.content}")
            await self.send_message("orchestrator", "final-response", f"Aggregated response from {message.content['from_sub_queen']}: {message.content['content']}", message.request_id)
        elif message.message_type == "response":
            print(f"QueenAgent received direct response from {message.sender_id}: {message.content}")
            await self.send_message("orchestrator", "final-response", f"Response from {message.sender_id}: {message.content}", message.request_id)
        elif message.message_type == "error":
            print(f"QueenAgent received error from {message.sender_id}: {message.content}")
            await self.send_message("orchestrator", "final-error", f"Error from {message.sender_id}: {message.content}", message.request_id)
