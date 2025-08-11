import asyncio
import json
import logging
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import concurrent.futures

from agents.base_agent import BaseAgent, AgentMessage
from agents.sub_queen_agent import SubQueenAgent
from agents.drone_agent import DroneAgent, DroneRole
from agents.secure_drone_agent import SecureDroneAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class TaskStatus(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class TaskNode:
    """Enhanced task representation with dependencies and metadata"""
    id: str
    content: str
    priority: TaskPriority
    estimated_duration: int  # seconds
    dependencies: List[str]  # IDs of tasks that must complete first
    required_skills: List[str]  # Skills needed to complete this task
    status: TaskStatus = TaskStatus.PENDING
    assigned_worker: Optional[str] = None
    created_at: float = 0.0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.created_at == 0.0:
            self.created_at = asyncio.get_event_loop().time()

class EnhancedQueenAgent(BaseAgent):
    """Enhanced Queen Agent with parallel task decomposition and intelligent scheduling"""
    
    def __init__(self, agent_id: str, name: str, architecture_type: str, model: str = "llama3", project_folder: str = None):
        super().__init__(agent_id, name)
        self.architecture_type = architecture_type
        self.model = model
        self.project_folder = project_folder or os.getcwd()
        self.sub_queen_agents: List[BaseAgent] = []
        self.drone_agents: List[BaseAgent] = []
        self.drone_roles: Dict[str, DroneRole] = {}  # agent_id -> role mapping
        
        # Enhanced task management
        self.task_graph: Dict[str, TaskNode] = {}
        self.active_tasks: Dict[str, str] = {}  # task_id -> worker_id
        self.completed_tasks: List[str] = []
        self.failed_tasks: List[str] = []
        
        # Performance metrics
        self.worker_performance: Dict[str, Dict[str, Any]] = {}
        self.task_execution_history: List[Dict[str, Any]] = []
        
        # Async executor for LLM calls
        self.llm_executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

    def initialize_agents(self):
        """Initialize available agents and their capabilities with load balancing"""
        if self.orchestrator:
            if self.architecture_type == 'HIERARCHICAL':
                # Enhanced Sub-Queen discovery and initialization
                from agents.enhanced_sub_queen_agent import EnhancedSubQueenAgent
                self.sub_queen_agents = self.orchestrator.get_agents_by_type(EnhancedSubQueenAgent)
                if not self.sub_queen_agents:
                    # Fallback to regular SubQueenAgent
                    self.sub_queen_agents = self.orchestrator.get_agents_by_type(SubQueenAgent)
                
                logger.info(f"QueenAgent {self.name} found {len(self.sub_queen_agents)} SubQueenAgents.")
                
                # Initialize Sub-Queen performance tracking
                self._initialize_subqueen_performance_tracking()
                
            elif self.architecture_type in ['CENTRALIZED', 'FULLY_CONNECTED']:
                # Try SecureDroneAgent first, fallback to DroneAgent
                self.drone_agents = self.orchestrator.get_agents_by_type(SecureDroneAgent)
                if not self.drone_agents:
                    self.drone_agents = self.orchestrator.get_agents_by_type(DroneAgent)
                logger.info(f"QueenAgent {self.name} found {len(self.drone_agents)} DroneAgents.")
                
                # Initialize drone performance tracking and roles
                self._initialize_drone_roles()
                for drone in self.drone_agents:
                    role = self.drone_roles.get(drone.agent_id, DroneRole.DEVELOPER)
                    skills = self._get_role_skills(role)
                    self.worker_performance[drone.agent_id] = {
                        'completed_tasks': 0,
                        'failed_tasks': 0,
                        'average_duration': 0.0,
                        'skills': skills,
                        'current_load': 0,
                        'reliability_score': 1.0,
                        'role': role.value
                    }
    
    def _initialize_subqueen_performance_tracking(self):
        """Initialize performance tracking for Sub-Queens"""
        for subqueen in self.sub_queen_agents:
            self.worker_performance[subqueen.agent_id] = {
                'completed_tasks': 0,
                'failed_tasks': 0,
                'average_duration': 0.0,
                'current_load': 0,
                'reliability_score': 1.0,
                'last_task_time': 0.0,
                'worker_count': 0,  # Number of workers managed by this sub-queen
                'available_workers': 0,  # Currently available workers
                'skills': ['general', 'management', 'coordination'],
                'response_time': 0.0
            }
            
        logger.info(f"Initialized performance tracking for {len(self.sub_queen_agents)} Sub-Queens")
    
    def _get_best_subqueen_for_task(self, task_node: TaskNode) -> Optional[str]:
        """Select best Sub-Queen for task using intelligent load balancing"""
        if not self.sub_queen_agents:
            return None
        
        # Get availability status from all Sub-Queens
        subqueen_scores = []
        
        for subqueen in self.sub_queen_agents:
            subqueen_id = subqueen.agent_id
            performance = self.worker_performance.get(subqueen_id, {})
            
            # Get real-time availability if Sub-Queen supports it
            availability_info = None
            if hasattr(subqueen, 'get_agent_availability_status'):
                try:
                    availability_info = subqueen.get_agent_availability_status()
                    # Update our tracking with real-time data
                    performance['available_workers'] = availability_info.get('available_agents', 0)
                    performance['worker_count'] = availability_info.get('total_agents', 0)
                    performance['utilization_rate'] = availability_info.get('utilization_rate', 0.0)
                except Exception as e:
                    logger.debug(f"Could not get availability status from Sub-Queen {subqueen_id}: {e}")
            
            # Skip Sub-Queens with no available workers
            available_workers = performance.get('available_workers', 1)  # Default to 1 if unknown
            if available_workers <= 0:
                logger.debug(f"Skipping Sub-Queen {subqueen_id}: no available workers")
                continue
            
            # Calculate load balancing score
            current_load = performance.get('current_load', 0)
            reliability = performance.get('reliability_score', 1.0)
            worker_count = performance.get('worker_count', 1)
            utilization_rate = performance.get('utilization_rate', current_load / max(worker_count, 1))
            
            # Score factors:
            # 1. Available capacity (more available workers = higher score)
            capacity_score = available_workers / max(worker_count, 1)
            
            # 2. Load balance (less utilized = higher score) 
            load_score = 1.0 - min(utilization_rate, 1.0)
            
            # 3. Reliability (historical success rate)
            reliability_score = reliability
            
            # 4. Response time (faster = higher score)
            response_time = performance.get('response_time', 1.0)
            speed_score = 1.0 / max(response_time, 0.1)
            
            # 5. Skill match for task
            skill_score = self._calculate_subqueen_skill_match(task_node, performance)
            
            # Weighted final score
            final_score = (
                capacity_score * 0.3 +      # 30% capacity
                load_score * 0.25 +         # 25% load balance
                reliability_score * 0.2 +   # 20% reliability
                speed_score * 0.15 +        # 15% speed
                skill_score * 0.1           # 10% skill match
            )
            
            subqueen_scores.append((subqueen_id, final_score, {
                'capacity_score': capacity_score,
                'load_score': load_score,
                'reliability_score': reliability_score,
                'available_workers': available_workers,
                'utilization_rate': utilization_rate
            }))
        
        if not subqueen_scores:
            logger.warning("No available Sub-Queens found for task assignment")
            return None
        
        # Sort by score (highest first)
        subqueen_scores.sort(key=lambda x: x[1], reverse=True)
        
        best_subqueen = subqueen_scores[0]
        best_id, best_score, best_metrics = best_subqueen
        
        logger.info(f"Selected Sub-Queen {best_id} for task (score: {best_score:.3f}, "
                   f"available workers: {best_metrics['available_workers']}, "
                   f"utilization: {best_metrics['utilization_rate']:.2%})")
        
        # Update load tracking
        self.worker_performance[best_id]['current_load'] += 1
        self.worker_performance[best_id]['last_task_time'] = asyncio.get_event_loop().time()
        
        return best_id
    
    def _calculate_subqueen_skill_match(self, task_node: TaskNode, subqueen_performance: Dict[str, Any]) -> float:
        """Calculate how well a Sub-Queen's skills match the task requirements"""
        subqueen_skills = set(subqueen_performance.get('skills', ['general']))
        required_skills = set(task_node.required_skills)
        
        if not required_skills:
            return 1.0  # No specific requirements
        
        # Calculate overlap
        skill_overlap = len(subqueen_skills.intersection(required_skills))
        skill_match = skill_overlap / len(required_skills)
        
        return skill_match
    
    async def _distribute_to_subqueens_with_fallback(self, task_nodes: List[TaskNode], request_id: str):
        """Distribute tasks to Sub-Queens with fallback mechanisms"""
        successful_assignments = []
        failed_assignments = []
        
        for task_node in task_nodes:
            success = False
            attempts = 0
            max_attempts = min(3, len(self.sub_queen_agents))  # Try up to 3 Sub-Queens
            
            while not success and attempts < max_attempts:
                attempts += 1
                
                # Get best available Sub-Queen
                best_subqueen = self._get_best_subqueen_for_task(task_node)
                
                if not best_subqueen:
                    logger.warning(f"Attempt {attempts}: No available Sub-Queen found for task {task_node.id}")
                    if attempts < max_attempts:
                        # Wait briefly and try again
                        await asyncio.sleep(1.0)
                        # Refresh Sub-Queen availability
                        self._refresh_subqueen_availability()
                        continue
                    else:
                        break
                
                try:
                    # Assign task to Sub-Queen
                    await self._assign_task_to_subqueen(best_subqueen, task_node, request_id)
                    successful_assignments.append((task_node.id, best_subqueen))
                    success = True
                    
                    logger.info(f"✅ Task {task_node.id} assigned to Sub-Queen {best_subqueen} (attempt {attempts})")
                    
                except Exception as e:
                    logger.warning(f"❌ Failed to assign task {task_node.id} to Sub-Queen {best_subqueen} (attempt {attempts}): {e}")
                    
                    # Mark Sub-Queen as temporarily unreliable
                    if best_subqueen in self.worker_performance:
                        self.worker_performance[best_subqueen]['reliability_score'] *= 0.8
                        self.worker_performance[best_subqueen]['current_load'] = max(0, 
                            self.worker_performance[best_subqueen]['current_load'] - 1)
                    
                    if attempts < max_attempts:
                        await asyncio.sleep(0.5)  # Brief delay before retry
                        continue
            
            if not success:
                failed_assignments.append(task_node.id)
                logger.error(f"💥 Failed to assign task {task_node.id} to any Sub-Queen after {attempts} attempts")
        
        # Log results
        logger.info(f"Task distribution results: {len(successful_assignments)} successful, {len(failed_assignments)} failed")
        
        # Handle failed assignments
        if failed_assignments:
            await self._handle_failed_task_assignments(failed_assignments, request_id)
        
        return successful_assignments, failed_assignments
    
    def _refresh_subqueen_availability(self):
        """Refresh availability data for all Sub-Queens"""
        for subqueen in self.sub_queen_agents:
            if hasattr(subqueen, 'get_agent_availability_status'):
                try:
                    availability = subqueen.get_agent_availability_status()
                    subqueen_id = subqueen.agent_id
                    
                    if subqueen_id in self.worker_performance:
                        self.worker_performance[subqueen_id].update({
                            'available_workers': availability.get('available_agents', 0),
                            'worker_count': availability.get('total_agents', 0),
                            'utilization_rate': availability.get('utilization_rate', 0.0)
                        })
                        
                except Exception as e:
                    logger.debug(f"Could not refresh availability for Sub-Queen {subqueen.agent_id}: {e}")
    
    async def _assign_task_to_subqueen(self, subqueen_id: str, task_node: TaskNode, request_id: str):
        """Assign task to specific Sub-Queen"""
        enhanced_content = f"""
        Enhanced Queen Task Assignment
        Task ID: {task_node.id}
        Priority: {task_node.priority.name}
        Estimated Duration: {task_node.estimated_duration}s
        Required Skills: {', '.join(task_node.required_skills)}
        Complexity Score: {task_node.metadata.get('complexity_score', 'N/A')}
        
        Task Content:
        {task_node.content}
        
        Sub-Queen Instructions:
        - This task has been optimized for your worker group
        - Use your enhanced availability checking and load balancing
        - Implement fallback mechanisms if workers become unavailable
        - Report back with detailed execution metrics
        """
        
        await self.send_message(subqueen_id, "sub-task-to-subqueen", enhanced_content, request_id)
        task_node.status = TaskStatus.ASSIGNED
        task_node.started_at = asyncio.get_event_loop().time()
        
        # Track assignment
        self.active_tasks[task_node.id] = subqueen_id
    
    async def _handle_failed_task_assignments(self, failed_task_ids: List[str], request_id: str):
        """Handle tasks that couldn't be assigned to any Sub-Queen"""
        if not failed_task_ids:
            return
        
        error_summary = {
            'failed_tasks': failed_task_ids,
            'total_failed': len(failed_task_ids),
            'sub_queen_status': {
                sq.agent_id: self.worker_performance.get(sq.agent_id, {})
                for sq in self.sub_queen_agents
            },
            'suggested_actions': [
                'Check Sub-Queen worker availability',
                'Consider adding more workers to Sub-Queens',
                'Review task complexity and decomposition',
                'Check for system resource constraints'
            ]
        }
        
        await self.send_message("orchestrator", "final-error", 
                              f"Failed to assign {len(failed_task_ids)} tasks to Sub-Queens: {json.dumps(error_summary)}", 
                              request_id)

    async def _async_ollama_call(self, prompt: str) -> str:
        """Make asynchronous Ollama API call"""
        loop = asyncio.get_event_loop()
        try:
            import ollama
            response = await loop.run_in_executor(
                self.llm_executor,
                lambda: ollama.chat(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}]
                )
            )
            return response["message"]["content"]
        except Exception as e:
            logger.error(f"Ollama API call failed: {e}")
            raise

    async def _intelligent_decompose_task(self, task: str, worker_count: int) -> List[TaskNode]:
        """Enhanced task decomposition with parallel analysis and dependency detection"""
        
        # Parallel decomposition with multiple LLM calls
        decomposition_tasks = [
            self._analyze_task_complexity(task),
            self._identify_task_dependencies(task),
            self._estimate_task_skills(task),
            self._generate_parallel_subtasks(task, worker_count)
        ]
        
        try:
            complexity_info, dependencies_info, skills_info, subtasks_raw = await asyncio.gather(
                *decomposition_tasks, return_exceptions=True
            )
            
            # Handle any exceptions in parallel calls
            if isinstance(subtasks_raw, Exception):
                logger.error(f"Subtask generation failed: {subtasks_raw}")
                subtasks_raw = [task]  # Fallback to original task
                
            # Parse and enhance subtasks
            subtasks = self._parse_subtasks_response(subtasks_raw)
            task_nodes = []
            
            for i, subtask in enumerate(subtasks):
                # Extract metadata from parallel analysis
                priority = self._determine_priority(subtask, complexity_info)
                estimated_duration = self._estimate_duration(subtask, complexity_info)
                dependencies = self._extract_dependencies(subtask, dependencies_info, i)
                required_skills = self._extract_skills(subtask, skills_info)
                
                task_node = TaskNode(
                    id=f"task_{len(self.task_graph)}_{i}",
                    content=subtask,
                    priority=priority,
                    estimated_duration=estimated_duration,
                    dependencies=dependencies,
                    required_skills=required_skills,
                    metadata={
                        'original_task': task,
                        'complexity_score': self._calculate_complexity_score(subtask, complexity_info),
                        'parallelizable': True
                    }
                )
                task_nodes.append(task_node)
                self.task_graph[task_node.id] = task_node
                
            logger.info(f"Decomposed task into {len(task_nodes)} parallel subtasks")
            return task_nodes
            
        except Exception as e:
            logger.error(f"Enhanced task decomposition failed: {e}")
            # Fallback to simple decomposition
            return await self._simple_fallback_decomposition(task)

    async def _analyze_task_complexity(self, task: str) -> Dict[str, Any]:
        """Analyze task complexity and resource requirements"""
        prompt = f"""Analyze the complexity of this task: '{task}'
        
        Respond with JSON containing:
        {{
            "complexity_level": "low|medium|high|critical",
            "estimated_time_minutes": number,
            "resource_requirements": ["cpu", "memory", "network", "disk"],
            "skill_level_required": "basic|intermediate|advanced|expert",
            "parallelizable_aspects": ["aspect1", "aspect2"]
        }}"""
        
        try:
            response = await self._async_ollama_call(prompt)
            return json.loads(response)
        except Exception as e:
            logger.warning(f"Complexity analysis failed: {e}")
            return {"complexity_level": "medium", "estimated_time_minutes": 5}

    async def _identify_task_dependencies(self, task: str) -> Dict[str, Any]:
        """Identify potential dependencies between subtasks"""
        prompt = f"""Identify dependencies for task decomposition: '{task}'
        
        Respond with JSON containing:
        {{
            "sequential_steps": ["step1", "step2", "step3"],
            "parallel_groups": [["task_a", "task_b"], ["task_c", "task_d"]],
            "prerequisites": ["requirement1", "requirement2"],
            "dependency_rules": [
                {{"task": "task_name", "depends_on": ["dep1", "dep2"]}}
            ]
        }}"""
        
        try:
            response = await self._async_ollama_call(prompt)
            return json.loads(response)
        except Exception as e:
            logger.warning(f"Dependency analysis failed: {e}")
            return {"sequential_steps": [], "parallel_groups": []}

    async def _estimate_task_skills(self, task: str) -> Dict[str, Any]:
        """Estimate required skills for task completion"""
        prompt = f"""Identify required skills for task: '{task}'
        
        Respond with JSON containing:
        {{
            "primary_skills": ["programming", "analysis", "research"],
            "secondary_skills": ["writing", "testing", "debugging"],
            "tools_required": ["python", "git", "docker"],
            "domain_knowledge": ["web_development", "data_science"]
        }}"""
        
        try:
            response = await self._async_ollama_call(prompt)
            return json.loads(response)
        except Exception as e:
            logger.warning(f"Skills analysis failed: {e}")
            return {"primary_skills": ["general"]}

    async def _generate_parallel_subtasks(self, task: str, worker_count: int) -> List[str]:
        """Generate subtasks optimized for parallel execution with command-line focus"""
        # Command-line focused task decomposition
        if "flask" in task.lower() and "app" in task.lower():
            return [
                f"Use command-line tools to create Flask application: {task}",
                "Execute any required setup commands and save the application",
                "Verify the created application works correctly"
            ]
        elif "web" in task.lower() and ("scraper" in task.lower() or "scraping" in task.lower()):
            return [
                f"Use command-line tools to create web scraper: {task}",
                "Install required dependencies and create the scraper code",
                "Test and save the completed scraper application"
            ]
        elif "api" in task.lower() and "rest" in task.lower():
            return [
                f"Use command-line tools to create REST API: {task}",
                "Set up the API structure and implement endpoints", 
                "Test the API and ensure it's properly saved"
            ]
        elif any(keyword in task.lower() for keyword in ["create", "build", "make", "develop", "generate"]):
            return [
                f"Analyze requirements and use appropriate command-line tools for: {task}",
                f"Execute the necessary commands to complete: {task}",
                f"Verify and finalize the implementation"
            ]
        else:
            # Generic command-line focused decomposition
            return [
                f"Use AI analysis and command-line tools to complete: {task}",
                f"Execute any required system commands and save results",
                f"Verify the task completion and provide feedback"
            ]

    def _extract_json_from_response(self, response: str):
        """Extract JSON from LLM response that may contain additional text"""
        import re
        
        # First try direct JSON parsing
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON array in the response
        json_patterns = [
            r'\[(.*?)\]',  # Look for array brackets
            r'```json\s*(\[.*?\])\s*```',  # JSON code blocks
            r'```\s*(\[.*?\])\s*```',  # Generic code blocks with arrays
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            for match in matches:
                try:
                    if pattern == r'\[(.*?)\]':
                        # Reconstruct the full array
                        json_str = '[' + match + ']'
                    else:
                        json_str = match
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    continue
        
        # Fallback: try to extract strings that look like task descriptions
        lines = response.strip().split('\n')
        tasks = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('//'):
                # Remove common prefixes
                line = re.sub(r'^[\d\.\-\*\+]+\s*', '', line)
                line = line.strip('"\'')
                if line and len(line) > 5:  # Reasonable task length
                    tasks.append(line)
        
        return tasks if tasks else [response.strip()]

    def _parse_subtasks_response(self, response: Any) -> List[str]:
        """Parse and validate subtasks response"""
        if isinstance(response, list):
            return [str(task) for task in response if task.strip()]
        elif isinstance(response, str):
            try:
                parsed = json.loads(response)
                if isinstance(parsed, list):
                    return [str(task) for task in parsed if task.strip()]
            except json.JSONDecodeError:
                pass
            return [response]
        else:
            return ["Failed to parse subtasks"]

    def _determine_priority(self, subtask: str, complexity_info: Dict[str, Any]) -> TaskPriority:
        """Determine task priority based on content and complexity"""
        complexity = complexity_info.get('complexity_level', 'medium').lower()
        
        # Priority keywords
        high_priority_keywords = ['critical', 'urgent', 'error', 'fix', 'security']
        medium_priority_keywords = ['implement', 'create', 'build', 'develop']
        
        subtask_lower = subtask.lower()
        
        if complexity == 'critical' or any(keyword in subtask_lower for keyword in high_priority_keywords):
            return TaskPriority.CRITICAL
        elif complexity == 'high':
            return TaskPriority.HIGH
        elif any(keyword in subtask_lower for keyword in medium_priority_keywords):
            return TaskPriority.MEDIUM
        else:
            return TaskPriority.LOW

    def _estimate_duration(self, subtask: str, complexity_info: Dict[str, Any]) -> int:
        """Estimate task duration in seconds"""
        base_duration = complexity_info.get('estimated_time_minutes', 5) * 60
        
        # Adjust based on task content
        if 'research' in subtask.lower():
            return int(base_duration * 1.5)
        elif 'test' in subtask.lower():
            return int(base_duration * 0.8)
        elif 'implement' in subtask.lower():
            return int(base_duration * 1.2)
        
        return base_duration

    def _extract_dependencies(self, subtask: str, dependencies_info: Dict[str, Any], task_index: int) -> List[str]:
        """Extract dependencies for a specific subtask"""
        dependency_rules = dependencies_info.get('dependency_rules', [])
        sequential_steps = dependencies_info.get('sequential_steps', [])
        
        dependencies = []
        
        # Check sequential dependencies
        if task_index > 0 and len(sequential_steps) > task_index:
            dependencies.append(f"task_{len(self.task_graph)}_{task_index-1}")
        
        return dependencies

    def _extract_skills(self, subtask: str, skills_info: Dict[str, Any]) -> List[str]:
        """Extract required skills for a subtask"""
        primary_skills = skills_info.get('primary_skills', ['general'])
        tools_required = skills_info.get('tools_required', [])
        
        # Combine skills based on subtask content
        required_skills = primary_skills.copy()
        
        subtask_lower = subtask.lower()
        if 'code' in subtask_lower or 'program' in subtask_lower:
            required_skills.extend(['programming'])
        if 'test' in subtask_lower:
            required_skills.extend(['testing'])
        if 'research' in subtask_lower:
            required_skills.extend(['research'])
            
        return list(set(required_skills))  # Remove duplicates

    def _calculate_complexity_score(self, subtask: str, complexity_info: Dict[str, Any]) -> float:
        """Calculate complexity score for a subtask"""
        base_score = {
            'low': 1.0,
            'medium': 2.0,
            'high': 3.0,
            'critical': 4.0
        }.get(complexity_info.get('complexity_level', 'medium'), 2.0)
        
        # Adjust based on subtask characteristics
        subtask_lower = subtask.lower()
        if 'complex' in subtask_lower or 'difficult' in subtask_lower:
            base_score *= 1.5
        elif 'simple' in subtask_lower or 'easy' in subtask_lower:
            base_score *= 0.8
            
        return min(base_score, 5.0)  # Cap at 5.0

    async def _simple_fallback_decomposition(self, task: str) -> List[TaskNode]:
        """Simple fallback decomposition when enhanced version fails"""
        try:
            prompt = f"Decompose '{task}' into 3-5 simple subtasks. Respond with JSON array of strings."
            response = await self._async_ollama_call(prompt)
            subtasks = json.loads(response)
            
            if not isinstance(subtasks, list):
                subtasks = [task]
                
            task_nodes = []
            for i, subtask in enumerate(subtasks):
                task_node = TaskNode(
                    id=f"fallback_task_{i}",
                    content=str(subtask),
                    priority=TaskPriority.MEDIUM,
                    estimated_duration=300,  # 5 minutes default
                    dependencies=[],
                    required_skills=['general']
                )
                task_nodes.append(task_node)
                
            return task_nodes
            
        except Exception as e:
            logger.error(f"Fallback decomposition failed: {e}")
            # Ultimate fallback - return original task
            return [TaskNode(
                id="ultimate_fallback",
                content=task,
                priority=TaskPriority.MEDIUM,
                estimated_duration=600,
                dependencies=[],
                required_skills=['general']
            )]

    def _get_optimal_drone_assignment(self, task_node: TaskNode) -> Optional[str]:
        """Intelligently assign tasks to drones based on roles, skills, load, and performance"""
        if not self.drone_agents:
            return None
            
        # Initialize drone performance tracking if missing
        for drone in self.drone_agents:
            if drone.agent_id not in self.worker_performance:
                role = self.drone_roles.get(drone.agent_id, DroneRole.DEVELOPER)
                skills = self._get_role_skills(role)
                self.worker_performance[drone.agent_id] = {
                    'completed_tasks': 0,
                    'failed_tasks': 0,
                    'average_duration': 0.0,
                    'skills': skills,
                    'current_load': 0,
                    'reliability_score': 1.0,
                    'role': role.value
                }
            
        # Determine optimal role for this task
        optimal_role = self._determine_task_role(task_node.content)
        
        available_drones = []
        for drone in self.drone_agents:
            drone_id = drone.agent_id
            performance = self.worker_performance[drone_id]
            drone_role = self.drone_roles.get(drone_id, DroneRole.DEVELOPER)
            
            # Role matching bonus
            role_match = 1.0 if drone_role == optimal_role else 0.5
            
            # Check if drone has required skills
            drone_skills = set(performance['skills'])
            required_skills = set(task_node.required_skills)
            
            skill_match = len(drone_skills.intersection(required_skills)) / len(required_skills) if required_skills else 1.0
            
            # Calculate drone score with role consideration
            score = (
                performance['reliability_score'] * 0.3 +
                skill_match * 0.25 +
                role_match * 0.3 +  # Role matching is important
                (1.0 - performance['current_load'] / 10.0) * 0.15  # Load consideration
            )
            
            available_drones.append((drone_id, score, drone_role))
            
        if not available_drones:
            return None
            
        # Sort by score and return best drone
        available_drones.sort(key=lambda x: x[1], reverse=True)
        best_drone_id = available_drones[0][0]
        best_role = available_drones[0][2]
        
        # Update drone role if needed and load
        if best_role != optimal_role:
            self.drone_roles[best_drone_id] = optimal_role
            # Update drone object if it supports role changes
            for drone in self.drone_agents:
                if drone.agent_id == best_drone_id and hasattr(drone, 'role'):
                    drone.role = optimal_role
                    if hasattr(drone, '_get_role_capabilities'):
                        drone.capabilities = drone._get_role_capabilities()
        
        self.worker_performance[best_drone_id]['current_load'] += 1
        
        return best_drone_id

    def _get_ready_tasks(self) -> List[TaskNode]:
        """Get tasks that are ready to be executed (dependencies met)"""
        ready_tasks = []
        
        for task_id, task_node in self.task_graph.items():
            if task_node.status != TaskStatus.PENDING:
                continue
                
            # Check if all dependencies are completed
            dependencies_met = all(
                dep_id in self.completed_tasks 
                for dep_id in task_node.dependencies
            )
            
            if dependencies_met:
                ready_tasks.append(task_node)
                
        # Sort by priority and estimated duration
        ready_tasks.sort(
            key=lambda t: (t.priority.value, -t.estimated_duration),
            reverse=True
        )
        
        return ready_tasks

    async def _distribute_tasks_optimally(self, task_nodes: List[TaskNode], request_id: str):
        """Distribute tasks optimally across available workers"""
        ready_tasks = self._get_ready_tasks()
        
        # Process ready tasks in parallel
        assignment_tasks = []
        
        for task_node in ready_tasks:
            if task_node.status == TaskStatus.PENDING:
                optimal_drone = self._get_optimal_drone_assignment(task_node)
                
                if optimal_drone:
                    task_node.status = TaskStatus.ASSIGNED
                    task_node.assigned_worker = optimal_drone  # Keep field name for compatibility
                    task_node.started_at = asyncio.get_event_loop().time()
                    
                    self.active_tasks[task_node.id] = optimal_drone
                    
                    # Create assignment task
                    assignment_task = self._assign_task_to_drone(
                        optimal_drone, task_node, request_id
                    )
                    assignment_tasks.append(assignment_task)
                    
                    logger.info(f"Assigned task {task_node.id} to drone {optimal_drone} with role {self.drone_roles.get(optimal_drone, 'unknown')}")
        
        # Execute all assignments in parallel
        if assignment_tasks:
            await asyncio.gather(*assignment_tasks, return_exceptions=True)

    async def _assign_task_to_drone(self, drone_id: str, task_node: TaskNode, request_id: str):
        """Assign a specific task to a drone with role-based context"""
        try:
            drone_role = self.drone_roles.get(drone_id, DroneRole.DEVELOPER)
            role_context = self._get_role_context(drone_role)
            
            enhanced_task_content = f"""
=== DRONE TASK ASSIGNMENT ===
Task ID: {task_node.id}
Drone Role: {drone_role.value.upper()}
Priority: {task_node.priority.name}
Estimated Duration: {task_node.estimated_duration}s
Required Skills: {', '.join(task_node.required_skills)}

=== ROLE CONTEXT ===
{role_context}

=== TASK DESCRIPTION ===
{task_node.content}

=== ADDITIONAL CONTEXT ===
- Complexity Score: {task_node.metadata.get('complexity_score', 'N/A')}
- Parallelizable: {task_node.metadata.get('parallelizable', True)}
- Original Task: {task_node.metadata.get('original_task', 'N/A')}

=== EXECUTION GUIDELINES ===
1. Apply role-specific expertise and methodologies
2. Consider task dependencies and prerequisites
3. Follow best practices for your assigned role
4. Document your approach and results
5. Report any issues or blockers immediately
            """
            
            await self.send_message(drone_id, "enhanced-task", enhanced_task_content, request_id)
            task_node.status = TaskStatus.IN_PROGRESS
            
        except Exception as e:
            logger.error(f"Failed to assign task {task_node.id} to drone {drone_id}: {e}")
            task_node.status = TaskStatus.FAILED
            self.failed_tasks.append(task_node.id)

    async def receive_message(self, message: AgentMessage):
        """Enhanced message handling with parallel task processing"""
        logger.info(f"QueenAgent {self.name} received {message.message_type} from {message.sender_id}")
        
        if message.message_type == "task":
            try:
                # Initialize agents if needed
                if not hasattr(self, '_agents_initialized'):
                    self.initialize_agents()
                    self._agents_initialized = True
                
                # Determine available worker count - fallback for HIERARCHICAL mode
                if self.architecture_type == 'HIERARCHICAL':
                    # If no sub-queens found, work directly with available workers
                    if len(self.sub_queen_agents) == 0:
                        logger.warning("No sub-queen agents found, falling back to direct drone mode")
                        if self.orchestrator:
                            # Try SecureDroneAgent first, fallback to DroneAgent
                            self.drone_agents = self.orchestrator.get_agents_by_type(SecureDroneAgent)
                            if not self.drone_agents:
                                self.drone_agents = self.orchestrator.get_agents_by_type(DroneAgent)
                            logger.info(f"Found {len(self.drone_agents)} drones for direct mode")
                            self._initialize_drone_roles()
                        worker_count = max(1, len(self.drone_agents))
                    else:
                        worker_count = len(self.sub_queen_agents) * 2
                elif self.architecture_type in ['CENTRALIZED', 'FULLY_CONNECTED']:
                    worker_count = len(self.drone_agents)
                else:
                    worker_count = 1  # Fallback
                
                # Check for simple file creation tasks first
                if self._is_simple_file_creation(message.content):
                    logger.info("Detected simple file creation task, executing directly")
                    await self._execute_task_directly(message.content, message.request_id)
                    return
                
                # Enhanced parallel task decomposition for complex tasks
                task_nodes = await self._intelligent_decompose_task(message.content, worker_count)
                
                logger.info(f"Decomposed into {len(task_nodes)} enhanced tasks with dependencies")
                
                # Distribution logic based on architecture
                if self.architecture_type == 'HIERARCHICAL' and len(self.sub_queen_agents) > 0:
                    # Use enhanced Sub-Queen distribution with fallbacks
                    logger.info("Using hierarchical distribution with enhanced Sub-Queens")
                    await self._distribute_to_subqueens_with_fallback(task_nodes, message.request_id)
                elif len(self.drone_agents) > 0:
                    # Direct drone distribution for centralized/fully-connected
                    logger.info("Using direct drone distribution")
                    await self._distribute_tasks_optimally(task_nodes, message.request_id)
                else:
                    # No agents available - execute task directly
                    logger.warning("No agents available, QueenAgent executing task directly")
                    await self._execute_task_directly(message.content, message.request_id)
                
            except Exception as e:
                logger.error(f"Task processing failed: {e}")
                await self.send_message("orchestrator", "final-error", f"Task processing failed: {e}", message.request_id)
                
        elif message.message_type in ["response", "error"]:
            # Handle task completion
            await self._handle_task_completion(message)
            
        elif message.message_type == "group-response":
            # Handle sub-queen responses
            await self._handle_group_response(message)

    async def _handle_task_completion(self, message: AgentMessage):
        """Handle task completion and update worker performance"""
        try:
            # Find completed task
            completed_task_id = None
            for task_id, worker_id in self.active_tasks.items():
                if worker_id == message.sender_id:
                    completed_task_id = task_id
                    break
                    
            if completed_task_id:
                task_node = self.task_graph[completed_task_id]
                current_time = asyncio.get_event_loop().time()
                
                if message.message_type == "response":
                    task_node.status = TaskStatus.COMPLETED
                    task_node.completed_at = current_time
                    self.completed_tasks.append(completed_task_id)
                    
                    # Update worker performance
                    worker_perf = self.worker_performance[message.sender_id]
                    worker_perf['completed_tasks'] += 1
                    worker_perf['current_load'] = max(0, worker_perf['current_load'] - 1)
                    
                    # Update average duration
                    actual_duration = current_time - task_node.started_at
                    prev_avg = worker_perf['average_duration']
                    completed_count = worker_perf['completed_tasks']
                    worker_perf['average_duration'] = (prev_avg * (completed_count - 1) + actual_duration) / completed_count
                    
                    logger.info(f"Task {completed_task_id} completed by {message.sender_id}")
                    
                else:  # error
                    task_node.status = TaskStatus.FAILED
                    self.failed_tasks.append(completed_task_id)
                    
                    # Update worker performance
                    worker_perf = self.worker_performance[message.sender_id]
                    worker_perf['failed_tasks'] += 1
                    worker_perf['current_load'] = max(0, worker_perf['current_load'] - 1)
                    worker_perf['reliability_score'] *= 0.9  # Reduce reliability
                    
                    logger.warning(f"Task {completed_task_id} failed on {message.sender_id}: {message.content}")
                
                # Remove from active tasks
                del self.active_tasks[completed_task_id]
                
                # Check if more tasks can be scheduled
                await self._schedule_pending_tasks(message.request_id)
                
                # Check if all tasks are complete
                await self._check_completion_status(message.request_id)
                
        except Exception as e:
            logger.error(f"Error handling task completion: {e}")

    async def _schedule_pending_tasks(self, request_id: str):
        """Schedule any newly available tasks"""
        ready_tasks = self._get_ready_tasks()
        if ready_tasks:
            await self._distribute_tasks_optimally(ready_tasks, request_id)

    async def _check_completion_status(self, request_id: str):
        """Check if all tasks are completed and send final response"""
        total_tasks = len(self.task_graph)
        completed_count = len(self.completed_tasks)
        failed_count = len(self.failed_tasks)
        active_count = len(self.active_tasks)
        
        if active_count == 0 and (completed_count + failed_count) == total_tasks:
            # All tasks finished
            success_rate = completed_count / total_tasks if total_tasks > 0 else 0
            
            final_response = {
                'status': 'completed',
                'total_tasks': total_tasks,
                'completed': completed_count,
                'failed': failed_count,
                'success_rate': success_rate,
                'execution_summary': self._generate_execution_summary()
            }
            
            if success_rate >= 0.8:  # 80% success threshold
                await self.send_message("orchestrator", "final-response", 
                                      f"All tasks completed successfully. {json.dumps(final_response)}", 
                                      request_id)
            else:
                await self.send_message("orchestrator", "final-error",
                                      f"Task execution completed with failures. {json.dumps(final_response)}",
                                      request_id)
            
            # Reset for next task
            self._reset_task_state()

    def _generate_execution_summary(self) -> Dict[str, Any]:
        """Generate execution summary with performance metrics"""
        return {
            'worker_performance': self.worker_performance,
            'total_execution_time': max([
                task.completed_at - task.created_at 
                for task in self.task_graph.values() 
                if task.completed_at
            ], default=0),
            'average_task_duration': sum([
                task.completed_at - task.started_at
                for task in self.task_graph.values()
                if task.completed_at and task.started_at
            ]) / max(len(self.completed_tasks), 1),
            'parallel_efficiency': len(self.completed_tasks) / len(self.drone_agents) if self.drone_agents else 0
        }

    def _reset_task_state(self):
        """Reset task state for next execution"""
        self.task_graph.clear()
        self.active_tasks.clear()
        self.completed_tasks.clear()
        self.failed_tasks.clear()
        
        # Reset drone loads but keep performance history
        for drone_id in self.worker_performance:
            self.worker_performance[drone_id]['current_load'] = 0

    async def _handle_group_response(self, message: AgentMessage):
        """Handle responses from sub-queen agents"""
        logger.info(f"Received group response from {message.sender_id}")
        content = message.content
        
        if isinstance(content, dict):
            original_sender = content.get('original_sender')
            response_type = content.get('type')
            response_content = content.get('content')
            
            # Treat as task completion
            mock_message = AgentMessage(
                sender_id=original_sender,
                receiver_id=self.agent_id,
                message_type=response_type,
                content=response_content,
                request_id=message.request_id
            )
            
            await self._handle_task_completion(mock_message)
        else:
            await self.send_message("orchestrator", "final-response", 
                                  f"Group response: {message.content}", 
                                  message.request_id)

    async def _execute_task_directly(self, task_content: str, request_id: str):
        """Execute task directly when no workers are available"""
        try:
            logger.info(f"QueenAgent executing task directly: {task_content[:50]}...")
            
            # Handle complex project creation (Helm Charts, etc.)
            if self._is_complex_project(task_content):
                await self._create_complex_project(task_content, request_id)
                return
            
            # Simple file creation logic without LLM for common cases
            if self._is_simple_file_creation(task_content):
                filename, content = self._extract_simple_file_info(task_content)
                if filename and content:
                    import os
                    project_folder = self.project_folder
                    file_path = os.path.join(project_folder, filename)
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    final_result = f"File created successfully: {file_path}\nContent: {content}"
                    logger.info(f"QueenAgent created file: {file_path}")
                    await self.send_message("orchestrator", "final-response", final_result, request_id)
                    return
            
            # Use Ollama for complex tasks
            file_creation_prompt = f"""
            Task: {task_content}
            
            Create a file. Respond with exactly this format:
            FILENAME: [filename]
            CONTENT:
            [file content here]
            """
            
            # Execute with Ollama
            result = await self._async_ollama_call(file_creation_prompt)
            
            # Parse the result to extract filename and content
            filename, content = self._parse_file_creation_result(result)
            
            if filename and content:
                # Create the file in the project directory
                import os
                project_folder = self.project_folder  # Use configured project folder
                file_path = os.path.join(project_folder, filename)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                final_result = f"File created successfully: {file_path}\nContent: {content}"
                logger.info(f"QueenAgent created file: {file_path}")
            else:
                final_result = f"Task completed: {result}"
            
            # Send final response
            await self.send_message("orchestrator", "final-response", final_result, request_id)
            
        except Exception as e:
            logger.error(f"Direct task execution failed: {e}")
            await self.send_message("orchestrator", "final-error", f"Direct task execution failed: {e}", request_id)
    
    def _parse_file_creation_result(self, result: str) -> tuple[str, str]:
        """Parse LLM result to extract filename and content"""
        import re
        
        # Look for FILENAME: pattern
        filename_match = re.search(r'FILENAME:\s*([^\n]+)', result, re.IGNORECASE)
        filename = filename_match.group(1).strip() if filename_match else None
        
        # Look for CONTENT: pattern
        content_match = re.search(r'CONTENT:\s*\n(.+)', result, re.DOTALL | re.IGNORECASE)
        content = content_match.group(1).strip() if content_match else None
        
        # Fallback: if no structured format, try to infer
        if not filename:
            # Look for common file patterns
            if "hallo welt" in result.lower() or "hello world" in result.lower():
                filename = "hello_world.txt" if not filename else filename
            else:
                filename = "output.txt"
        
        if not content:
            # Use the whole result as content if no structured content found
            content = result.strip()
            
        return filename, content
    
    def _is_simple_file_creation(self, task_content: str) -> bool:
        """Check if this is a file creation task that should be handled directly"""
        task_lower = task_content.lower()
        
        # Look for file creation patterns
        file_keywords = ['create', 'erstelle', 'make', 'write', 'save', 'speichere']
        
        # Comprehensive list of common file extensions
        file_extensions = [
            # Text and Documents
            '.txt', '.md', '.rst', '.doc', '.docx', '.pdf', '.rtf', '.odt',
            
            # Programming Languages
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
            '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.r',
            '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd',
            
            # Web Technologies
            '.html', '.htm', '.css', '.scss', '.sass', '.less', '.xml', '.xhtml',
            '.svg', '.vue', '.angular', '.react',
            
            # Data Formats
            '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.properties',
            '.csv', '.tsv', '.xlsx', '.xls', '.ods', '.sql', '.db', '.sqlite',
            
            # Images
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp', '.ico',
            '.psd', '.ai', '.eps', '.raw', '.cr2', '.nef', '.orf',
            
            # Audio/Video
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma',
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v',
            
            # Archives
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.tar.gz', '.tar.bz2',
            
            # Config and System
            '.env', '.gitignore', '.gitattributes', '.editorconfig', '.dockerignore',
            '.htaccess', '.robots', '.sitemap', '.manifest',
            
            # DevOps and Infrastructure
            '.dockerfile', '.docker-compose', '.k8s', '.helm', '.terraform', '.tf',
            '.ansible', '.vagrant', '.makefile', '.cmake', '.gradle',
            
            # Logs and Temp
            '.log', '.tmp', '.temp', '.cache', '.bak', '.backup', '.old', '.orig',
            
            # Fonts
            '.ttf', '.otf', '.woff', '.woff2', '.eot',
            
            # eBooks
            '.epub', '.mobi', '.azw', '.azw3', '.fb2',
            
            # CAD and 3D
            '.dwg', '.dxf', '.step', '.iges', '.stl', '.obj', '.3ds', '.blend',
            
            # Science and Engineering  
            '.mat', '.csv', '.dat', '.nc', '.hdf5', '.fits', '.nii',
            
            # Mobile
            '.apk', '.ipa', '.aab'
        ]
        
        has_file_keyword = any(keyword in task_lower for keyword in file_keywords)
        has_file_extension = any(ext in task_lower for ext in file_extensions)
        has_filename = any(word.endswith(tuple(file_extensions)) for word in task_content.split())
        
        # Also check for "file" keyword
        has_file_word = 'file' in task_lower or 'datei' in task_lower
        
        # Check for complex project types that should NOT be handled as simple file creation
        complex_projects = ['helm', 'helmchart', 'docker', 'kubernetes', 'k8s', 'pentest', 'penetration', 'security', 'tool', 'framework', 'system', 'application', 'app', 'website', 'web']
        has_complex_project = any(project in task_lower for project in complex_projects)
        
        # If it's a complex project, it should NOT be treated as simple file creation
        if has_complex_project:
            return False
            
        return has_file_keyword and (has_file_extension or has_filename or has_file_word)
    
    def _extract_simple_file_info(self, task_content: str) -> tuple[str, str]:
        """Extract filename and content from simple file creation tasks"""
        import re
        
        # Extract filename
        filename = None
        words = task_content.split()
        
        # Comprehensive file extensions list (same as above)
        all_extensions = [
            '.txt', '.md', '.rst', '.doc', '.docx', '.pdf', '.rtf', '.odt',
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
            '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.r',
            '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd',
            '.html', '.htm', '.css', '.scss', '.sass', '.less', '.xml', '.xhtml',
            '.svg', '.vue', '.angular', '.react',
            '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.properties',
            '.csv', '.tsv', '.xlsx', '.xls', '.ods', '.sql', '.db', '.sqlite',
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp', '.ico',
            '.psd', '.ai', '.eps', '.raw', '.cr2', '.nef', '.orf',
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma',
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v',
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.tar.gz', '.tar.bz2',
            '.env', '.gitignore', '.gitattributes', '.editorconfig', '.dockerignore',
            '.htaccess', '.robots', '.sitemap', '.manifest',
            '.dockerfile', '.docker-compose', '.k8s', '.helm', '.terraform', '.tf',
            '.ansible', '.vagrant', '.makefile', '.cmake', '.gradle',
            '.log', '.tmp', '.temp', '.cache', '.bak', '.backup', '.old', '.orig',
            '.ttf', '.otf', '.woff', '.woff2', '.eot',
            '.epub', '.mobi', '.azw', '.azw3', '.fb2',
            '.dwg', '.dxf', '.step', '.iges', '.stl', '.obj', '.3ds', '.blend',
            '.mat', '.dat', '.nc', '.hdf5', '.fits', '.nii', '.apk', '.ipa', '.aab'
        ]
        
        # Look for files with extensions
        for word in words:
            if any(word.lower().endswith(ext) for ext in all_extensions):
                filename = word.strip('"\'')
                break
        
        # Also look for "as filename" pattern with all extensions
        extension_pattern = '|'.join(ext[1:] for ext in all_extensions)  # Remove dots for regex
        as_match = re.search(rf'\bas\s+([^\s]+\.(?:{extension_pattern}))', task_content, re.IGNORECASE)
        if as_match and not filename:
            filename = as_match.group(1).strip()
        
        # Extract content patterns
        content_patterns = [
            r'(?:content|inhalt|mit)\s+["\']([^"\']+)["\']',
            r'(?:content|inhalt):\s*([^\n]+)',
            r'(?:text|content|inhalt)\s+(.+?)(?:\s|$)',
        ]
        
        content = None
        for pattern in content_patterns:
            match = re.search(pattern, task_content, re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                break
        
        # Fallback values
        if not filename:
            if 'hallo' in task_content.lower() or 'hello' in task_content.lower():
                filename = 'hello.txt'
            else:
                filename = 'output.txt'
        
        if not content:
            if 'hallo' in task_content.lower():
                content = 'Hallo Welt!'
            elif 'hello' in task_content.lower():
                content = 'Hello World!'
            elif 'bible' in task_content.lower():
                content = 'This would be Bible content - for copyright reasons, please refer to an actual Bible source.'
            else:
                content = 'File content created by Ollama Flow'
        
        return filename, content
    
    def _is_complex_project(self, task_content: str) -> bool:
        """Check if this is a complex project creation task"""
        task_lower = task_content.lower()
        
        # Look for complex project patterns
        create_keywords = ['create', 'erstelle', 'make', 'generate']
        complex_projects = ['helm', 'helmchart', 'docker', 'kubernetes', 'k8s']
        
        has_create_keyword = any(keyword in task_lower for keyword in create_keywords)
        has_complex_project = any(project in task_lower for project in complex_projects)
        
        return has_create_keyword and has_complex_project
    
    async def _create_complex_project(self, task_content: str, request_id: str):
        """Create complex projects like Helm Charts"""
        try:
            task_lower = task_content.lower()
            
            if 'helm' in task_lower:
                await self._create_helm_chart(task_content, request_id)
            elif 'docker' in task_lower:
                await self._create_docker_project(task_content, request_id)
            else:
                await self.send_message("orchestrator", "final-error", 
                                      f"Unsupported complex project type in: {task_content}", 
                                      request_id)
                
        except Exception as e:
            logger.error(f"Complex project creation failed: {e}")
            await self.send_message("orchestrator", "final-error", 
                                  f"Complex project creation failed: {e}", 
                                  request_id)
    
    async def _create_helm_chart(self, task_content: str, request_id: str):
        """Create a complete Helm Chart structure"""
        try:
            import os
            
            # Determine chart name
            chart_name = "nginx-chart"
            if 'nginx' in task_content.lower():
                chart_name = "nginx-chart"
            elif 'apache' in task_content.lower():
                chart_name = "apache-chart"
            
            project_folder = self.project_folder
            chart_path = os.path.join(project_folder, chart_name)
            
            # Create chart directory structure
            os.makedirs(chart_path, exist_ok=True)
            os.makedirs(os.path.join(chart_path, "templates"), exist_ok=True)
            os.makedirs(os.path.join(chart_path, "charts"), exist_ok=True)
            
            # Create Chart.yaml
            chart_yaml = f"""apiVersion: v2
name: {chart_name}
description: A Helm chart for NGINX
type: application
version: 0.1.0
appVersion: "1.0"
"""
            
            # Create values.yaml
            values_yaml = """# Default values for nginx-chart
replicaCount: 1

image:
  repository: nginx
  pullPolicy: IfNotPresent
  tag: "latest"

nameOverride: ""
fullnameOverride: ""

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: false
  className: ""
  annotations: {}
  hosts:
    - host: chart-example.local
      paths:
        - path: /
          pathType: Prefix
  tls: []

resources: {}

nodeSelector: {}

tolerations: []

affinity: {}
"""
            
            # Create deployment template
            deployment_yaml = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "nginx-chart.fullname" . }}
  labels:
    {{- include "nginx-chart.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "nginx-chart.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "nginx-chart.selectorLabels" . | nindent 8 }}
    spec:
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: 80
              protocol: TCP
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
"""
            
            # Create service template
            service_yaml = """apiVersion: v1
kind: Service
metadata:
  name: {{ include "nginx-chart.fullname" . }}
  labels:
    {{- include "nginx-chart.labels" . | nindent 4 }}
spec:
  type: {{ .Values.service.type }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: http
      protocol: TCP
      name: http
  selector:
    {{- include "nginx-chart.selectorLabels" . | nindent 4 }}
"""
            
            # Create helpers template
            helpers_yaml = '''{{/*
Expand the name of the chart.
*/}}
{{- define "nginx-chart.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "nginx-chart.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "nginx-chart.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "nginx-chart.labels" -}}
helm.sh/chart: {{ include "nginx-chart.chart" . }}
{{ include "nginx-chart.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "nginx-chart.selectorLabels" -}}
app.kubernetes.io/name: {{ include "nginx-chart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
'''
            
            # Write all files
            with open(os.path.join(chart_path, "Chart.yaml"), 'w') as f:
                f.write(chart_yaml)
            
            with open(os.path.join(chart_path, "values.yaml"), 'w') as f:
                f.write(values_yaml)
                
            with open(os.path.join(chart_path, "templates", "deployment.yaml"), 'w') as f:
                f.write(deployment_yaml)
                
            with open(os.path.join(chart_path, "templates", "service.yaml"), 'w') as f:
                f.write(service_yaml)
                
            with open(os.path.join(chart_path, "templates", "_helpers.tpl"), 'w') as f:
                f.write(helpers_yaml)
                
            # Create .helmignore
            helmignore = """# Patterns to ignore when building packages.
# This supports shell glob matching, relative path matching, and
# negation (prefixed with !). Only one pattern per line.
.DS_Store
# Common VCS dirs
.git/
.gitignore
.bzr/
.bzrignore
.hg/
.hgignore
.svn/
# Common backup files
*.swp
*.bak
*.tmp
*.orig
*~
# Various IDEs
.project
.idea/
*.tmproj
.vscode/
"""
            
            with open(os.path.join(chart_path, ".helmignore"), 'w') as f:
                f.write(helmignore)
            
            files_created = [
                f"{chart_name}/Chart.yaml",
                f"{chart_name}/values.yaml", 
                f"{chart_name}/templates/deployment.yaml",
                f"{chart_name}/templates/service.yaml",
                f"{chart_name}/templates/_helpers.tpl",
                f"{chart_name}/.helmignore"
            ]
            
            final_result = f"""Helm Chart created successfully!

Chart Name: {chart_name}
Location: {chart_path}

Files created:
{chr(10).join('- ' + file for file in files_created)}

To use this chart:
1. helm install my-nginx ./{chart_name}
2. helm upgrade my-nginx ./{chart_name}
3. helm uninstall my-nginx

Chart is ready for deployment!"""
            
            logger.info(f"QueenAgent created Helm Chart: {chart_path}")
            await self.send_message("orchestrator", "final-response", final_result, request_id)
            
        except Exception as e:
            logger.error(f"Helm Chart creation failed: {e}")
            await self.send_message("orchestrator", "final-error", f"Helm Chart creation failed: {e}", request_id)
    
    async def _create_docker_project(self, task_content: str, request_id: str):
        """Create a Docker project structure"""
        try:
            import os
            
            project_folder = self.project_folder
            
            # Create Dockerfile
            dockerfile_content = """FROM nginx:alpine

# Copy custom configuration if needed
# COPY nginx.conf /etc/nginx/nginx.conf

# Copy static content
# COPY ./html /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
"""
            
            # Create docker-compose.yml
            compose_content = """version: '3.8'

services:
  nginx:
    build: .
    ports:
      - "80:80"
    volumes:
      - ./html:/usr/share/nginx/html:ro
    restart: unless-stopped
"""
            
            with open(os.path.join(project_folder, "Dockerfile"), 'w') as f:
                f.write(dockerfile_content)
                
            with open(os.path.join(project_folder, "docker-compose.yml"), 'w') as f:
                f.write(compose_content)
            
            # Create html directory with index.html
            html_dir = os.path.join(project_folder, "html")
            os.makedirs(html_dir, exist_ok=True)
            
            index_html = """<!DOCTYPE html>
<html>
<head>
    <title>Welcome to nginx!</title>
</head>
<body>
    <h1>Welcome to nginx!</h1>
    <p>If you see this page, the nginx web server is successfully installed and working.</p>
</body>
</html>
"""
            
            with open(os.path.join(html_dir, "index.html"), 'w') as f:
                f.write(index_html)
            
            final_result = f"""Docker project created successfully!

Files created:
- Dockerfile
- docker-compose.yml
- html/index.html

To use this project:
1. docker build -t my-nginx .
2. docker run -p 80:80 my-nginx
   OR
3. docker-compose up

Your NGINX server will be available at http://localhost"""
            
            logger.info(f"QueenAgent created Docker project in: {project_folder}")
            await self.send_message("orchestrator", "final-response", final_result, request_id)
            
        except Exception as e:
            logger.error(f"Docker project creation failed: {e}")
            await self.send_message("orchestrator", "final-error", f"Docker project creation failed: {e}", request_id)

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
                    
    def _get_role_skills(self, role: DroneRole) -> List[str]:
        """Get skills associated with a specific role"""
        role_skills = {
            DroneRole.ANALYST: [
                "data_analysis", "report_generation", "pattern_recognition",
                "statistical_analysis", "visualization", "documentation"
            ],
            DroneRole.DATA_SCIENTIST: [
                "machine_learning", "data_preprocessing", "model_training",
                "feature_engineering", "statistical_modeling", "python_analysis"
            ],
            DroneRole.IT_ARCHITECT: [
                "system_design", "infrastructure_planning", "scalability_design",
                "security_architecture", "technology_selection", "diagram_creation"
            ],
            DroneRole.DEVELOPER: [
                "coding", "debugging", "testing", "deployment",
                "version_control", "code_review", "problem_solving"
            ]
        }
        return role_skills.get(role, ['general'])
        
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
        
    def _get_role_context(self, role: DroneRole) -> str:
        """Get context description for a specific role"""
        role_contexts = {
            DroneRole.ANALYST: "Focus on data analysis, pattern recognition, and generating comprehensive reports with actionable insights.",
            DroneRole.DATA_SCIENTIST: "Focus on machine learning, statistical analysis, data preprocessing, and data-driven insights using scientific methodologies.",
            DroneRole.IT_ARCHITECT: "Focus on system design, scalability, security architecture, and infrastructure planning with enterprise-grade solutions.",
            DroneRole.DEVELOPER: "Focus on coding, implementation, testing, and creating functional, maintainable software solutions."
        }
        return role_contexts.get(role, "Complete the assigned task with professional expertise.")
        
    def get_drone_status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report of all drones and their roles"""
        drone_status = []
        for drone in self.drone_agents:
            role = self.drone_roles.get(drone.agent_id, DroneRole.DEVELOPER)
            performance = self.worker_performance.get(drone.agent_id, {})
            
            drone_status.append({
                'agent_id': drone.agent_id,
                'name': drone.name,
                'role': role.value,
                'skills': self._get_role_skills(role),
                'current_load': performance.get('current_load', 0),
                'completed_tasks': performance.get('completed_tasks', 0),
                'failed_tasks': performance.get('failed_tasks', 0),
                'reliability_score': performance.get('reliability_score', 1.0)
            })
            
        return {
            'total_drones': len(self.drone_agents),
            'role_distribution': {role.value: sum(1 for r in self.drone_roles.values() if r == role) for role in DroneRole},
            'active_tasks': len(self.active_tasks),
            'completed_tasks': len(self.completed_tasks),
            'failed_tasks': len(self.failed_tasks),
            'drone_details': drone_status
        }

    def __del__(self):
        """Cleanup executor on destruction"""
        if hasattr(self, 'llm_executor'):
            self.llm_executor.shutdown(wait=False)