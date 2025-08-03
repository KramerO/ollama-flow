import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import concurrent.futures

from agents.base_agent import BaseAgent, AgentMessage
from agents.sub_queen_agent import SubQueenAgent
from agents.worker_agent import WorkerAgent

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
    
    def __init__(self, agent_id: str, name: str, architecture_type: str, model: str = "llama3"):
        super().__init__(agent_id, name)
        self.architecture_type = architecture_type
        self.model = model
        self.sub_queen_agents: List[BaseAgent] = []
        self.worker_agents: List[BaseAgent] = []
        
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
        """Initialize available agents and their capabilities"""
        if self.orchestrator:
            if self.architecture_type == 'HIERARCHICAL':
                self.sub_queen_agents = self.orchestrator.get_agents_by_type(SubQueenAgent)
                logger.info(f"QueenAgent {self.name} found {len(self.sub_queen_agents)} SubQueenAgents.")
            elif self.architecture_type in ['CENTRALIZED', 'FULLY_CONNECTED']:
                self.worker_agents = self.orchestrator.get_agents_by_type(WorkerAgent)
                logger.info(f"QueenAgent {self.name} found {len(self.worker_agents)} WorkerAgents.")
                
                # Initialize worker performance tracking
                for worker in self.worker_agents:
                    self.worker_performance[worker.agent_id] = {
                        'completed_tasks': 0,
                        'failed_tasks': 0,
                        'average_duration': 0.0,
                        'skills': ['general'],  # Default skills
                        'current_load': 0,
                        'reliability_score': 1.0
                    }

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
        """Generate subtasks optimized for parallel execution"""
        prompt = f"""Decompose this task into {worker_count} parallel subtasks: '{task}'
        
        Requirements:
        1. Tasks should be independent and parallelizable
        2. Each task should take similar time to complete  
        3. Minimize dependencies between tasks
        4. Focus on maximizing worker utilization
        5. Each subtask should be atomic and complete
        
        Respond with JSON array of strings:
        ["Independent subtask 1", "Independent subtask 2", ...]
        
        Aim for {worker_count} subtasks to match available workers."""
        
        try:
            response = await self._async_ollama_call(prompt)
            subtasks = json.loads(response)
            if isinstance(subtasks, list) and all(isinstance(item, str) for item in subtasks):
                return subtasks
            else:
                raise ValueError("Invalid response format")
        except Exception as e:
            logger.error(f"Parallel subtask generation failed: {e}")
            return [task]  # Fallback

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

    def _get_optimal_worker_assignment(self, task_node: TaskNode) -> Optional[str]:
        """Intelligently assign tasks to workers based on skills, load, and performance"""
        if not self.worker_agents:
            return None
            
        available_workers = []
        for worker in self.worker_agents:
            worker_id = worker.agent_id
            performance = self.worker_performance[worker_id]
            
            # Check if worker has required skills
            worker_skills = set(performance['skills'])
            required_skills = set(task_node.required_skills)
            
            skill_match = len(worker_skills.intersection(required_skills)) / len(required_skills)
            
            # Calculate worker score
            score = (
                performance['reliability_score'] * 0.4 +
                skill_match * 0.3 +
                (1.0 - performance['current_load'] / 10.0) * 0.3  # Prefer less loaded workers
            )
            
            available_workers.append((worker_id, score))
            
        if not available_workers:
            return None
            
        # Sort by score and return best worker
        available_workers.sort(key=lambda x: x[1], reverse=True)
        best_worker_id = available_workers[0][0]
        
        # Update worker load
        self.worker_performance[best_worker_id]['current_load'] += 1
        
        return best_worker_id

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
                optimal_worker = self._get_optimal_worker_assignment(task_node)
                
                if optimal_worker:
                    task_node.status = TaskStatus.ASSIGNED
                    task_node.assigned_worker = optimal_worker
                    task_node.started_at = asyncio.get_event_loop().time()
                    
                    self.active_tasks[task_node.id] = optimal_worker
                    
                    # Create assignment task
                    assignment_task = self._assign_task_to_worker(
                        optimal_worker, task_node, request_id
                    )
                    assignment_tasks.append(assignment_task)
                    
                    logger.info(f"Assigned task {task_node.id} to worker {optimal_worker}")
        
        # Execute all assignments in parallel
        if assignment_tasks:
            await asyncio.gather(*assignment_tasks, return_exceptions=True)

    async def _assign_task_to_worker(self, worker_id: str, task_node: TaskNode, request_id: str):
        """Assign a specific task to a worker"""
        try:
            enhanced_task_content = f"""
            Task ID: {task_node.id}
            Priority: {task_node.priority.name}
            Estimated Duration: {task_node.estimated_duration}s
            Required Skills: {', '.join(task_node.required_skills)}
            
            Task: {task_node.content}
            
            Additional Context:
            - Complexity Score: {task_node.metadata.get('complexity_score', 'N/A')}
            - Parallelizable: {task_node.metadata.get('parallelizable', True)}
            - Original Task: {task_node.metadata.get('original_task', 'N/A')}
            """
            
            await self.send_message(worker_id, "enhanced-task", enhanced_task_content, request_id)
            task_node.status = TaskStatus.IN_PROGRESS
            
        except Exception as e:
            logger.error(f"Failed to assign task {task_node.id} to worker {worker_id}: {e}")
            task_node.status = TaskStatus.FAILED
            self.failed_tasks.append(task_node.id)

    async def receive_message(self, message: AgentMessage):
        """Enhanced message handling with parallel task processing"""
        logger.info(f"QueenAgent {self.name} received {message.message_type} from {message.sender_id}")
        
        if message.message_type == "task":
            try:
                # Determine available worker count
                worker_count = len(self.worker_agents) if self.architecture_type in ['CENTRALIZED', 'FULLY_CONNECTED'] else len(self.sub_queen_agents) * 2
                
                # Enhanced parallel task decomposition
                task_nodes = await self._intelligent_decompose_task(message.content, worker_count)
                
                logger.info(f"Decomposed into {len(task_nodes)} enhanced tasks with dependencies")
                
                # Optimal task distribution
                await self._distribute_tasks_optimally(task_nodes, message.request_id)
                
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
            'parallel_efficiency': len(self.completed_tasks) / len(self.worker_agents) if self.worker_agents else 0
        }

    def _reset_task_state(self):
        """Reset task state for next execution"""
        self.task_graph.clear()
        self.active_tasks.clear()
        self.completed_tasks.clear()
        self.failed_tasks.clear()
        
        # Reset worker loads but keep performance history
        for worker_id in self.worker_performance:
            self.worker_performance[worker_id]['current_load'] = 0

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

    def __del__(self):
        """Cleanup executor on destruction"""
        if hasattr(self, 'llm_executor'):
            self.llm_executor.shutdown(wait=False)