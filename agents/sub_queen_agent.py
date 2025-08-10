import ollama
import asyncio
import json
from typing import List, Type, Optional

from agents.base_agent import BaseAgent, AgentMessage
from agents.drone_agent import DroneAgent, DroneRole
from agents.secure_drone_agent import SecureDroneAgent
from typing import Dict

# Import enhanced JSON parser
try:
    from enhanced_json_parser import parse_subtasks
    ENHANCED_PARSER_AVAILABLE = True
except ImportError:
    ENHANCED_PARSER_AVAILABLE = False
    print("⚠️ Enhanced JSON parser not available, using fallback")

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
            
            # Use enhanced JSON parser if available
            if ENHANCED_PARSER_AVAILABLE:
                try:
                    subtasks = parse_subtasks(raw_response)
                    if subtasks and len(subtasks) > 0:
                        print(f"[SubQueenAgent] ✅ Enhanced parser successfully extracted {len(subtasks)} subtasks")
                        return subtasks
                    else:
                        print(f"[SubQueenAgent] ⚠️ Enhanced parser returned empty result, using fallback")
                except Exception as e:
                    print(f"[SubQueenAgent] ⚠️ Enhanced parser failed: {e}, using fallback")
            
            # Fallback to robust parsing method
            subtasks = self._parse_subtasks_robust(raw_response)
            if subtasks:
                return subtasks
            else:
                print(f"[SubQueenAgent] All parsing strategies failed. Falling back to single task.")
                return [task]
                
        except Exception as e:
            print(f"[SubQueenAgent] Error during task decomposition: {e}. Falling back to single task.")
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
                print(f"[SubQueenAgent] Strategy 1 successful: {len(subtasks)} subtasks")
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
                    print(f"[SubQueenAgent] Strategy 2 successful: {len(items)} subtasks")
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
                print(f"[SubQueenAgent] Strategy 3 successful: {len(subtasks)} subtasks")
                return subtasks
        except:
            pass
            
        print("[SubQueenAgent] All parsing strategies failed")
        return None

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

                # Use round-robin to select drone (role will be assigned dynamically by the drone)
                target_drone = self.group_drone_agents[self.current_agent_index]
                self.current_agent_index = (self.current_agent_index + 1) % len(self.group_drone_agents)

                # Send task directly - drone will assign its own role dynamically
                print(f"SubQueenAgent {self.name} delegating task to {target_drone.name} ({target_drone.agent_id}) for dynamic role assignment")
                await self.send_message(target_drone.agent_id, "sub-task", subtask, message.request_id)

        elif message.message_type == "response" or message.message_type == "error":
            print(f"SubQueenAgent {self.name} received {message.message_type} from {message.sender_id}: {message.content}")
            await self.send_message("queen-agent-1", "group-response", {
                "from_sub_queen": self.agent_id,
                "original_sender": message.sender_id,
                "type": message.message_type,
                "content": message.content,
            }, message.request_id)
            
    def _initialize_drone_roles(self):
        """Initialize drone roles for available drones (dynamic assignment system)"""
        print(f"[SubQueenAgent] {len(self.group_drone_agents)} drones initialized with dynamic role assignment capability")
                    
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
            DroneRole.DEVELOPER: "As a developer drone, focus on coding, implementation, testing, and creating functional solutions.",
            DroneRole.SECURITY_SPECIALIST: "As a security specialist drone, focus on identifying vulnerabilities, implementing secure coding practices, conducting security audits, and ensuring compliance with security standards."
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
