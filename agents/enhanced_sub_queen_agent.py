import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import concurrent.futures

from agents.base_agent import BaseAgent, AgentMessage
from agents.secure_drone_agent import SecureDroneAgent
from agents.enhanced_queen_agent import TaskNode, TaskPriority, TaskStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedSubQueenAgent(BaseAgent):
    """Enhanced Sub-Queen Agent with parallel processing and intelligent task management"""
    
    def __init__(self, agent_id: str, name: str, model: str = "llama3"):
        super().__init__(agent_id, name)
        self.model = model
        self.group_worker_agents: List[SecureDroneAgent] = []
        
        # Enhanced task management
        self.task_queue: List[TaskNode] = []
        self.active_tasks: Dict[str, str] = {}  # task_id -> worker_id
        self.completed_tasks: List[str] = []
        self.failed_tasks: List[str] = []
        
        # Worker performance tracking
        self.worker_performance: Dict[str, Dict[str, Any]] = {}
        
        # Async executor for LLM calls
        self.llm_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        
        # Current request tracking
        self.current_request_id: Optional[str] = None
        self.parent_queen_id: Optional[str] = None

    def initialize_group_agents(self, agents: List[SecureDroneAgent]):
        """Initialize drone agents with performance tracking"""
        self.group_worker_agents = agents
        logger.info(f"SubQueenAgent {self.name} initialized with {len(agents)} DroneAgents.")
        
        # Initialize performance tracking for each drone
        for drone in agents:
            self.worker_performance[drone.agent_id] = {
                'completed_tasks': 0,
                'failed_tasks': 0,
                'average_duration': 0.0,
                'skills': ['general', 'programming', 'analysis'],  # Default skills
                'current_load': 0,
                'reliability_score': 1.0,
                'response_time': 0.0
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

    async def _enhanced_decompose_task(self, task: str) -> List[TaskNode]:
        """Enhanced task decomposition optimized for worker group"""
        worker_count = len(self.group_worker_agents)
        
        if worker_count == 0:
            logger.warning("No workers available for task decomposition")
            return []
        
        # Parallel analysis tasks
        analysis_tasks = [
            self._analyze_subtask_complexity(task),
            self._generate_worker_optimized_subtasks(task, worker_count),
            self._identify_worker_skills_match(task)
        ]
        
        try:
            complexity_info, subtasks_raw, skills_match = await asyncio.gather(
                *analysis_tasks, return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(subtasks_raw, Exception):
                logger.error(f"Subtask generation failed: {subtasks_raw}")
                subtasks_raw = [task]
            
            # Parse subtasks
            subtasks = self._parse_subtasks_response(subtasks_raw)
            
            # Create enhanced task nodes
            task_nodes = []
            for i, subtask in enumerate(subtasks):
                task_node = TaskNode(
                    id=f"subqueen_{self.agent_id}_task_{i}",
                    content=subtask,
                    priority=self._determine_priority(subtask, complexity_info),
                    estimated_duration=self._estimate_duration(subtask, complexity_info),
                    dependencies=[],  # Sub-queen tasks are typically independent
                    required_skills=self._extract_required_skills(subtask, skills_match),
                    metadata={
                        'sub_queen_id': self.agent_id,
                        'worker_group_size': worker_count,
                        'complexity_score': self._calculate_complexity_score(subtask, complexity_info),
                        'optimized_for_workers': True
                    }
                )
                task_nodes.append(task_node)
                
            logger.info(f"SubQueen {self.name} decomposed task into {len(task_nodes)} worker-optimized subtasks")
            return task_nodes
            
        except Exception as e:
            logger.error(f"Enhanced task decomposition failed: {e}")
            return await self._fallback_decomposition(task)

    async def _analyze_subtask_complexity(self, task: str) -> Dict[str, Any]:
        """Analyze complexity specific to worker capabilities"""
        prompt = f"""Analyze this subtask for worker execution: '{task}'
        
        Consider:
        1. Can this be completed by a single worker?
        2. What's the complexity level for an individual worker?
        3. What resources/tools are needed?
        4. How long should this take for one worker?
        
        Respond with JSON:
        {{
            "worker_complexity": "simple|moderate|complex|expert",
            "estimated_minutes": number,
            "resources_needed": ["tool1", "tool2"],
            "single_worker_capable": true/false,
            "skill_level": "basic|intermediate|advanced"
        }}"""
        
        try:
            response = await self._async_ollama_call(prompt)
            return json.loads(response)
        except Exception as e:
            logger.warning(f"Complexity analysis failed: {e}")
            return {
                "worker_complexity": "moderate",
                "estimated_minutes": 3,
                "single_worker_capable": True
            }

    async def _generate_worker_optimized_subtasks(self, task: str, worker_count: int) -> List[str]:
        """Generate subtasks optimized for available workers"""
        prompt = f"""Break down this task for {worker_count} workers: '{task}'
        
        Requirements:
        1. Each subtask should be completable by ONE worker independently
        2. Tasks should be roughly equal in difficulty and time
        3. Minimize coordination needed between workers
        4. Each task should be specific and actionable
        5. Optimize for parallel execution
        
        Generate exactly {min(worker_count, 6)} subtasks (don't exceed available workers).
        
        Respond with JSON array: ["specific subtask 1", "specific subtask 2", ...]"""
        
        try:
            response = await self._async_ollama_call(prompt)
            subtasks = json.loads(response)
            
            if isinstance(subtasks, list) and all(isinstance(item, str) for item in subtasks):
                # Limit to available workers
                return subtasks[:worker_count]
            else:
                raise ValueError("Invalid subtasks format")
                
        except Exception as e:
            logger.error(f"Worker-optimized subtask generation failed: {e}")
            return [task]  # Fallback to original task

    async def _identify_worker_skills_match(self, task: str) -> Dict[str, Any]:
        """Identify which worker skills are needed for the task"""
        prompt = f"""Identify skills needed for task: '{task}'
        
        Focus on practical skills a worker agent would need:
        - programming languages
        - tools and frameworks  
        - domain knowledge
        - technical capabilities
        
        Respond with JSON:
        {{
            "required_skills": ["skill1", "skill2"],
            "preferred_skills": ["skill3", "skill4"],
            "difficulty_level": "beginner|intermediate|advanced|expert"
        }}"""
        
        try:
            response = await self._async_ollama_call(prompt)
            return json.loads(response)
        except Exception as e:
            logger.warning(f"Skills analysis failed: {e}")
            return {"required_skills": ["general"], "difficulty_level": "intermediate"}

    def _parse_subtasks_response(self, response: Any) -> List[str]:
        """Parse and validate subtasks response"""
        if isinstance(response, list):
            return [str(task).strip() for task in response if str(task).strip()]
        elif isinstance(response, str):
            try:
                parsed = json.loads(response)
                if isinstance(parsed, list):
                    return [str(task).strip() for task in parsed if str(task).strip()]
            except json.JSONDecodeError:
                pass
            # If not JSON, treat as single task
            return [response.strip()] if response.strip() else []
        else:
            return []

    def _determine_priority(self, subtask: str, complexity_info: Dict[str, Any]) -> TaskPriority:
        """Determine priority based on complexity and content"""
        complexity = complexity_info.get('worker_complexity', 'moderate').lower()
        single_worker = complexity_info.get('single_worker_capable', True)
        
        # High priority for complex tasks that need expert attention
        if complexity == 'expert' or not single_worker:
            return TaskPriority.HIGH
        elif complexity == 'complex':
            return TaskPriority.MEDIUM
        else:
            return TaskPriority.LOW

    def _estimate_duration(self, subtask: str, complexity_info: Dict[str, Any]) -> int:
        """Estimate duration based on complexity analysis"""
        base_minutes = complexity_info.get('estimated_minutes', 3)
        
        # Adjust based on complexity
        complexity = complexity_info.get('worker_complexity', 'moderate').lower()
        multiplier = {
            'simple': 0.8,
            'moderate': 1.0,
            'complex': 1.5,
            'expert': 2.0
        }.get(complexity, 1.0)
        
        return int(base_minutes * multiplier * 60)  # Convert to seconds

    def _extract_required_skills(self, subtask: str, skills_match: Dict[str, Any]) -> List[str]:
        """Extract required skills for the subtask"""
        required_skills = skills_match.get('required_skills', ['general'])
        preferred_skills = skills_match.get('preferred_skills', [])
        
        # Combine required and some preferred skills
        all_skills = required_skills + preferred_skills[:2]  # Limit preferred skills
        
        return list(set(all_skills))  # Remove duplicates

    def _calculate_complexity_score(self, subtask: str, complexity_info: Dict[str, Any]) -> float:
        """Calculate complexity score for worker assignment"""
        complexity_map = {
            'simple': 1.0,
            'moderate': 2.0,
            'complex': 3.0,
            'expert': 4.0
        }
        
        base_score = complexity_map.get(
            complexity_info.get('worker_complexity', 'moderate').lower(),
            2.0
        )
        
        # Adjust if not single-worker capable
        if not complexity_info.get('single_worker_capable', True):
            base_score *= 1.5
            
        return min(base_score, 5.0)

    async def _fallback_decomposition(self, task: str) -> List[TaskNode]:
        """Fallback decomposition when enhanced version fails"""
        try:
            # Simple decomposition
            subtasks = [task]  # Keep as single task
            
            task_node = TaskNode(
                id=f"fallback_{self.agent_id}",
                content=task,
                priority=TaskPriority.MEDIUM,
                estimated_duration=180,  # 3 minutes
                dependencies=[],
                required_skills=['general'],
                metadata={'fallback': True}
            )
            
            return [task_node]
            
        except Exception as e:
            logger.error(f"Fallback decomposition failed: {e}")
            return []

    def _get_optimal_worker(self, task_node: TaskNode) -> Optional[str]:
        """Select optimal worker for task based on skills and performance"""
        if not self.group_worker_agents:
            return None
            
        worker_scores = []
        
        for worker in self.group_worker_agents:
            worker_id = worker.agent_id
            performance = self.worker_performance[worker_id]
            
            # Skip if worker is overloaded
            if performance['current_load'] >= 3:  # Max 3 concurrent tasks
                continue
                
            # Calculate skill match
            worker_skills = set(performance['skills'])
            required_skills = set(task_node.required_skills)
            
            if required_skills:
                skill_match = len(worker_skills.intersection(required_skills)) / len(required_skills)
            else:
                skill_match = 1.0  # No specific requirements
                
            # Calculate worker score
            load_factor = 1.0 - (performance['current_load'] / 3.0)  # Prefer less loaded
            reliability = performance['reliability_score']
            
            score = (
                skill_match * 0.4 +
                reliability * 0.3 +
                load_factor * 0.3
            )
            
            worker_scores.append((worker_id, score))
            
        if not worker_scores:
            return None
            
        # Return best worker
        worker_scores.sort(key=lambda x: x[1], reverse=True)
        best_worker = worker_scores[0][0]
        
        # Update load
        self.worker_performance[best_worker]['current_load'] += 1
        
        return best_worker

    async def _distribute_tasks_to_workers(self, task_nodes: List[TaskNode], request_id: str):
        """Distribute tasks to workers optimally"""
        self.task_queue.extend(task_nodes)
        
        # Process tasks in parallel
        assignment_tasks = []
        
        for task_node in task_nodes:
            optimal_worker = self._get_optimal_worker(task_node)
            
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
                
                logger.info(f"SubQueen {self.name} assigned {task_node.id} to {optimal_worker}")
            else:
                logger.warning(f"No available worker for task {task_node.id}")
                task_node.status = TaskStatus.FAILED
                self.failed_tasks.append(task_node.id)
        
        # Execute assignments in parallel
        if assignment_tasks:
            await asyncio.gather(*assignment_tasks, return_exceptions=True)

    async def _assign_task_to_worker(self, worker_id: str, task_node: TaskNode, request_id: str):
        """Assign specific task to worker"""
        try:
            enhanced_content = f"""
            SubQueen Assignment from {self.name}
            Task ID: {task_node.id}
            Priority: {task_node.priority.name}
            Estimated Duration: {task_node.estimated_duration}s
            Required Skills: {', '.join(task_node.required_skills)}
            
            Task: {task_node.content}
            
            Context:
            - Optimized for single worker execution
            - Complexity Score: {task_node.metadata.get('complexity_score', 'N/A')}
            - Worker Group: {task_node.metadata.get('worker_group_size', 'N/A')} total workers
            """
            
            await self.send_message(worker_id, "sub-task", enhanced_content, request_id)
            task_node.status = TaskStatus.IN_PROGRESS
            
        except Exception as e:
            logger.error(f"Failed to assign task {task_node.id} to {worker_id}: {e}")
            task_node.status = TaskStatus.FAILED
            self.failed_tasks.append(task_node.id)

    async def receive_message(self, message: AgentMessage):
        """Enhanced message handling with availability checking and fallbacks"""
        logger.info(f"SubQueenAgent {self.name} received {message.message_type} from {message.sender_id}")
        
        # Store current request context
        self.current_request_id = message.request_id
        
        if message.message_type == "sub-task-to-subqueen":
            try:
                # Extract parent queen ID
                self.parent_queen_id = message.sender_id
                
                # Check agent availability BEFORE processing
                available_drones = self._check_worker_availability()
                
                if not available_drones:
                    # No drones available - use fallback mechanism
                    await self._handle_no_workers_available(message)
                    return
                
                logger.info(f"SubQueen {self.name}: {len(available_drones)}/{len(self.group_worker_agents)} drones available")
                
                # Enhanced task decomposition
                task_nodes = await self._enhanced_decompose_task(message.content)
                
                if task_nodes:
                    # Distribute to workers
                    await self._distribute_tasks_to_workers(task_nodes, message.request_id)
                else:
                    # No tasks created - send error
                    await self.send_message(
                        message.sender_id, 
                        "error", 
                        f"Failed to decompose task: {message.content}", 
                        message.request_id
                    )
                    
            except Exception as e:
                logger.error(f"SubQueen task processing failed: {e}")
                await self.send_message(
                    message.sender_id, 
                    "error", 
                    f"Task processing failed: {e}", 
                    message.request_id
                )
                
        elif message.message_type in ["response", "error"]:
            # Handle worker completion
            await self._handle_worker_completion(message)
    
    def _check_worker_availability(self) -> List[str]:
        """Check which drones are currently available"""
        available_drones = []
        
        for drone in self.group_worker_agents:
            drone_id = drone.agent_id
            performance = self.worker_performance.get(drone_id, {})
            
            # Consider drone available if:
            # 1. Current load is not at maximum
            # 2. Reliability score is acceptable
            current_load = performance.get('current_load', 0)
            reliability = performance.get('reliability_score', 1.0)
            
            if current_load < 3 and reliability > 0.3:  # Max 3 tasks, min 30% reliability
                available_drones.append(drone_id)
        
        return available_drones
    
    async def _handle_no_workers_available(self, message: AgentMessage):
        """Handle scenario when no drones are available - implement fallback mechanisms"""
        logger.warning(f"⚠️ SubQueen {self.name}: No drones available for task")
        
        # Fallback strategy 1: Wait briefly and retry
        logger.info("Trying fallback strategy 1: Wait and retry...")
        await asyncio.sleep(2.0)  # Wait 2 seconds
        
        available_drones = self._check_worker_availability()
        if available_drones:
            logger.info(f"✅ After waiting: {len(available_drones)} drones became available")
            # Retry task processing
            await self.receive_message(message)
            return
        
        # Fallback strategy 2: Reset overloaded drones with lower reliability
        logger.info("Trying fallback strategy 2: Reset overloaded drones...")
        reset_count = self._reset_overloaded_workers()
        
        if reset_count > 0:
            logger.info(f"✅ Reset {reset_count} overloaded drones")
            # Retry task processing
            available_drones = self._check_worker_availability()
            if available_drones:
                await self.receive_message(message)
                return
        
        # Fallback strategy 3: Lower standards temporarily
        logger.info("Trying fallback strategy 3: Lower reliability standards...")
        emergency_drones = self._get_emergency_workers()
        
        if emergency_drones:
            logger.info(f"✅ Found {len(emergency_drones)} emergency drones")
            # Temporarily update drone availability
            for drone_id in emergency_drones:
                if drone_id in self.worker_performance:
                    self.worker_performance[drone_id]['current_load'] = max(0, 
                        self.worker_performance[drone_id]['current_load'] - 1)
            
            # Retry task processing
            await self.receive_message(message)
            return
        
        # Final fallback: Report error back to orchestrator with detailed info
        error_msg = {
            "error": "No DroneAgents available",
            "sub_queen": self.name,
            "total_drones": len(self.group_worker_agents),
            "drone_status": {
                drone_id: {
                    "current_load": perf.get("current_load", 0),
                    "reliability": perf.get("reliability_score", 1.0),
                    "failed_tasks": perf.get("failed_tasks", 0)
                }
                for drone_id, perf in self.worker_performance.items()
            },
            "fallback_attempts": ["wait_retry", "reset_overloaded", "lower_standards"],
            "suggestion": "Consider redistributing task to another Sub-Queen or reducing task complexity"
        }
        
        await self.send_message(
            message.sender_id,
            "group-response",
            {
                "from_sub_queen": self.agent_id,
                "original_sender": self.agent_id,
                "type": "error",
                "content": f"No DroneAgents in group for Sub Queen {self.name}: {json.dumps(error_msg)}"
            },
            message.request_id
        )
    
    def _reset_overloaded_workers(self) -> int:
        """Reset drones that are overloaded but have low reliability"""
        reset_count = 0
        
        for drone_id, performance in self.worker_performance.items():
            current_load = performance.get('current_load', 0)
            reliability = performance.get('reliability_score', 1.0)
            failed_tasks = performance.get('failed_tasks', 0)
            
            # Reset if overloaded AND (low reliability OR many failures)
            if current_load >= 3 and (reliability < 0.6 or failed_tasks > 5):
                logger.info(f"🔄 Resetting overloaded drone {drone_id} (load: {current_load}, reliability: {reliability:.2f})")
                performance['current_load'] = 0
                performance['reliability_score'] = min(1.0, reliability + 0.1)  # Small boost
                reset_count += 1
        
        return reset_count
    
    def _get_emergency_workers(self) -> List[str]:
        """Get drones with very low standards for emergency situations"""
        emergency_drones = []
        
        for drone in self.group_worker_agents:
            drone_id = drone.agent_id
            performance = self.worker_performance.get(drone_id, {})
            
            # Emergency standards: accept almost any drone except completely broken ones
            current_load = performance.get('current_load', 0)
            reliability = performance.get('reliability_score', 1.0)
            
            if current_load < 5 and reliability > 0.1:  # Very low standards
                emergency_drones.append(drone_id)
        
        return emergency_drones

    async def _handle_worker_completion(self, message: AgentMessage):
        """Handle worker task completion"""
        try:
            # Find completed task
            completed_task_id = None
            for task_id, worker_id in self.active_tasks.items():
                if worker_id == message.sender_id:
                    completed_task_id = task_id
                    break
                    
            if not completed_task_id:
                logger.warning(f"No active task found for worker {message.sender_id}")
                return
                
            # Find task node
            task_node = None
            for node in self.task_queue:
                if node.id == completed_task_id:
                    task_node = node
                    break
                    
            if not task_node:
                logger.error(f"Task node not found for {completed_task_id}")
                return
                
            current_time = asyncio.get_event_loop().time()
            
            # Update task status
            if message.message_type == "response":
                task_node.status = TaskStatus.COMPLETED
                task_node.completed_at = current_time
                self.completed_tasks.append(completed_task_id)
                
                # Update worker performance
                worker_perf = self.worker_performance[message.sender_id]
                worker_perf['completed_tasks'] += 1
                worker_perf['current_load'] = max(0, worker_perf['current_load'] - 1)
                
                # Update response time
                if task_node.started_at:
                    duration = current_time - task_node.started_at
                    prev_avg = worker_perf['average_duration']
                    count = worker_perf['completed_tasks']
                    worker_perf['average_duration'] = (prev_avg * (count - 1) + duration) / count
                
                logger.info(f"SubQueen {self.name}: Task {completed_task_id} completed")
                
            else:  # error
                task_node.status = TaskStatus.FAILED
                self.failed_tasks.append(completed_task_id)
                
                # Update worker performance
                worker_perf = self.worker_performance[message.sender_id]
                worker_perf['failed_tasks'] += 1
                worker_perf['current_load'] = max(0, worker_perf['current_load'] - 1)
                worker_perf['reliability_score'] *= 0.9  # Reduce reliability
                
                logger.warning(f"SubQueen {self.name}: Task {completed_task_id} failed")
            
            # Remove from active tasks
            del self.active_tasks[completed_task_id]
            
            # Check if all tasks are complete
            await self._check_completion_status()
            
        except Exception as e:
            logger.error(f"Error handling worker completion: {e}")

    async def _check_completion_status(self):
        """Check if all tasks are completed and report to parent Queen"""
        total_tasks = len(self.task_queue)
        completed_count = len(self.completed_tasks)
        failed_count = len(self.failed_tasks)
        active_count = len(self.active_tasks)
        
        if active_count == 0 and (completed_count + failed_count) == total_tasks and total_tasks > 0:
            # All tasks finished
            success_rate = completed_count / total_tasks
            
            summary = {
                'sub_queen_id': self.agent_id,
                'total_tasks': total_tasks,
                'completed': completed_count,
                'failed': failed_count,
                'success_rate': success_rate,
                'worker_performance': self.worker_performance,
                'execution_time': max([
                    task.completed_at - task.created_at
                    for task in self.task_queue
                    if task.completed_at
                ], default=0)
            }
            
            # Send result to parent Queen
            if self.parent_queen_id and self.current_request_id:
                if success_rate >= 0.7:  # 70% success threshold for sub-queens
                    await self.send_message(
                        self.parent_queen_id,
                        "group-response",
                        {
                            "from_sub_queen": self.agent_id,
                            "original_sender": self.agent_id,
                            "type": "response",
                            "content": f"SubQueen tasks completed. Summary: {json.dumps(summary)}"
                        },
                        self.current_request_id
                    )
                else:
                    await self.send_message(
                        self.parent_queen_id,
                        "group-response", 
                        {
                            "from_sub_queen": self.agent_id,
                            "original_sender": self.agent_id,
                            "type": "error",
                            "content": f"SubQueen tasks completed with failures. Summary: {json.dumps(summary)}"
                        },
                        self.current_request_id
                    )
            
            # Reset for next batch
            self._reset_task_state()

    def _reset_task_state(self):
        """Reset task state for next execution"""
        self.task_queue.clear()
        self.active_tasks.clear()
        self.completed_tasks.clear()
        self.failed_tasks.clear()
        self.current_request_id = None
        self.parent_queen_id = None
        
        # Reset worker loads
        for worker_id in self.worker_performance:
            self.worker_performance[worker_id]['current_load'] = 0

    def get_agent_availability_status(self) -> Dict[str, Any]:
        """Get current availability status for queen agent"""
        total_agents = len(self.group_worker_agents)
        available_agents = len(self._check_worker_availability())
        
        utilization_rate = 0.0
        if total_agents > 0:
            busy_agents = total_agents - available_agents
            utilization_rate = busy_agents / total_agents
        
        return {
            'total_agents': total_agents,
            'available_agents': available_agents,
            'busy_agents': total_agents - available_agents,
            'utilization_rate': utilization_rate,
            'active_tasks': len(self.active_tasks),
            'completed_tasks': len(self.completed_tasks),
            'failed_tasks': len(self.failed_tasks),
            'performance_summary': self.worker_performance
        }

    def __del__(self):
        """Cleanup executor on destruction"""
        if hasattr(self, 'llm_executor'):
            self.llm_executor.shutdown(wait=False)