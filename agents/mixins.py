"""
Mixins for common agent functionality to reduce code duplication
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import json
import logging
import asyncio
import os
import re

from exceptions import TaskDecompositionException, AgentCommunicationException, ValidationException
from llm_backend import EnhancedLLMBackendManager


class TaskDecompositionMixin:
    """Mixin for agents that need task decomposition capabilities"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = getattr(self, 'logger', logging.getLogger(f"{__name__}.{getattr(self, 'agent_id', 'unknown')}"))
    
    async def decompose_task(self, 
                           task: str, 
                           context: str = "", 
                           max_subtasks: int = 10,
                           agent_type: str = "generic") -> List[str]:
        """Decompose a task into actionable subtasks"""
        prompt = self._build_decomposition_prompt(task, context, max_subtasks, agent_type)
        
        try:
            backend_manager = EnhancedLLMBackendManager()
            response = await backend_manager.generate(
                prompt=prompt,
                model=getattr(self, 'model', 'llama3')
            )
            
            return self._parse_decomposition_response(response.content, task, max_subtasks)
            
        except Exception as e:
            self.logger.error(f"Task decomposition failed: {e}")
            raise TaskDecompositionException(f"Failed to decompose task: {e}")
    
    def _build_decomposition_prompt(self, task: str, context: str, max_subtasks: int, agent_type: str) -> str:
        """Build the decomposition prompt based on agent type"""
        base_prompt = f"""
Task: {task}
Context: {context}

Decompose this into at most {max_subtasks} smaller, actionable subtasks suitable for {agent_type} agents.
Each subtask should be specific and executable.

Requirements:
- Return ONLY a JSON array of strings
- Each string should be a clear, actionable subtask
- Subtasks should be ordered logically
- Maximum {max_subtasks} subtasks

Example format: ["Subtask 1", "Subtask 2", "Subtask 3"]
        """
        
        # Add agent-specific instructions
        if agent_type == "worker":
            base_prompt += """
Additional requirements for worker agents:
- Include file operations if needed (create, modify, execute)
- Specify exact commands or code to generate
- Consider dependencies between subtasks
            """
        elif agent_type == "coordinator":
            base_prompt += """
Additional requirements for coordinator agents:
- Focus on orchestration and delegation
- Include validation and quality checks
- Consider parallel execution opportunities
            """
        
        return base_prompt.strip()
    
    def _parse_decomposition_response(self, response: str, fallback_task: str, max_subtasks: int) -> List[str]:
        """Parse LLM response into subtasks list with error handling"""
        # Clean the response
        response = response.strip()
        
        # Try to find JSON array in the response
        json_patterns = [
            response,  # Direct JSON
            self._extract_json_from_text(response),  # Extract from markdown or text
        ]
        
        for pattern in json_patterns:
            if pattern:
                try:
                    subtasks = json.loads(pattern)
                    if isinstance(subtasks, list) and all(isinstance(item, str) for item in subtasks):
                        # Validate and clean subtasks
                        valid_subtasks = []
                        for subtask in subtasks[:max_subtasks]:
                            cleaned = subtask.strip()
                            if cleaned and len(cleaned) > 5:  # Minimum meaningful length
                                valid_subtasks.append(cleaned)
                        
                        if valid_subtasks:
                            self.logger.info(f"Successfully decomposed task into {len(valid_subtasks)} subtasks")
                            return valid_subtasks
                            
                except json.JSONDecodeError:
                    continue
        
        # If parsing fails, try to extract tasks from lines
        fallback_subtasks = self._extract_tasks_from_lines(response)
        if fallback_subtasks:
            return fallback_subtasks[:max_subtasks]
        
        # Final fallback
        self.logger.warning("Task decomposition parsing failed, using original task")
        return [fallback_task]
    
    def _extract_json_from_text(self, text: str) -> Optional[str]:
        """Extract JSON array from text that might contain markdown or other content"""
        # Look for JSON array patterns
        import re
        
        # Pattern for JSON array
        json_pattern = r'\[(?:[^[\]]|(?:\[[^[\]]*\]))*\]'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            # Verify it looks like a string array
            if '"' in match and ',' in match:
                return match.strip()
        
        return None
    
    def _extract_tasks_from_lines(self, text: str) -> List[str]:
        """Extract tasks from line-based text as fallback"""
        lines = text.split('\n')
        tasks = []
        
        for line in lines:
            line = line.strip()
            # Look for numbered lists, bullet points, or simple sentences
            if any(line.startswith(prefix) for prefix in ['1.', '2.', '3.', '4.', '5.', '-', '*', '•']):
                # Remove the prefix and clean
                cleaned = re.sub(r'^[\d\.\-\*\•\s]+', '', line).strip()
                if len(cleaned) > 10:  # Meaningful task length
                    tasks.append(cleaned)
            elif len(line) > 15 and '.' in line and not line.startswith(('Example', 'Note', 'Format')):
                # Looks like a sentence that could be a task
                tasks.append(line)
        
        return tasks[:5]  # Limit fallback tasks


class MessageHandlingMixin:
    """Mixin for consistent message handling patterns"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = getattr(self, 'logger', logging.getLogger(f"{__name__}.{getattr(self, 'agent_id', 'unknown')}"))
    
    async def handle_error_message(self, message):
        """Standard error message handling"""
        error_content = getattr(message, 'content', str(message))
        sender_id = getattr(message, 'sender_id', 'unknown')
        request_id = getattr(message, 'request_id', None)
        
        self.logger.error(f"Received error from {sender_id}: {error_content}")
        
        try:
            await self.send_message(
                "orchestrator", 
                "final-error", 
                f"Error from {sender_id}: {error_content}",
                request_id
            )
        except Exception as e:
            self.logger.error(f"Failed to forward error message: {e}")
            raise AgentCommunicationException(f"Failed to send error response: {e}")
    
    async def handle_response_message(self, message):
        """Standard response message handling"""
        response_content = getattr(message, 'content', str(message))
        sender_id = getattr(message, 'sender_id', 'unknown')
        request_id = getattr(message, 'request_id', None)
        
        self.logger.info(f"Received response from {sender_id}")
        
        try:
            await self.send_message(
                "orchestrator",
                "final-response", 
                f"Response from {sender_id}: {response_content}",
                request_id
            )
        except Exception as e:
            self.logger.error(f"Failed to forward response message: {e}")
            raise AgentCommunicationException(f"Failed to send response: {e}")
    
    async def send_message_with_retry(self, 
                                    receiver_id: str, 
                                    message_type: str, 
                                    content: str, 
                                    request_id: Optional[str] = None,
                                    max_retries: int = 3,
                                    retry_delay: float = 1.0):
        """Send message with retry logic"""
        for attempt in range(max_retries):
            try:
                await self.send_message(receiver_id, message_type, content, request_id)
                return
            except Exception as e:
                self.logger.warning(f"Message send attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    raise AgentCommunicationException(f"Failed to send message after {max_retries} attempts: {e}")


class PerformanceTrackingMixin:
    """Mixin for tracking agent performance metrics"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.performance_metrics = {
            'tasks_processed': 0,
            'tasks_successful': 0,
            'tasks_failed': 0,
            'avg_processing_time': 0.0,
            'total_processing_time': 0.0
        }
        self.logger = getattr(self, 'logger', logging.getLogger(f"{__name__}.{getattr(self, 'agent_id', 'unknown')}"))
    
    async def track_task_performance(self, task_func, *args, **kwargs):
        """Decorator-like function to track task performance"""
        import time
        start_time = time.time()
        
        try:
            result = await task_func(*args, **kwargs)
            
            # Record success
            duration = time.time() - start_time
            self.performance_metrics['tasks_processed'] += 1
            self.performance_metrics['tasks_successful'] += 1
            self.performance_metrics['total_processing_time'] += duration
            
            # Update average
            total_tasks = self.performance_metrics['tasks_processed']
            self.performance_metrics['avg_processing_time'] = (
                self.performance_metrics['total_processing_time'] / total_tasks
            )
            
            self.logger.debug(f"Task completed in {duration:.2f}s")
            return result
            
        except Exception as e:
            # Record failure
            duration = time.time() - start_time
            self.performance_metrics['tasks_processed'] += 1
            self.performance_metrics['tasks_failed'] += 1
            self.performance_metrics['total_processing_time'] += duration
            
            # Update average
            total_tasks = self.performance_metrics['tasks_processed']
            self.performance_metrics['avg_processing_time'] = (
                self.performance_metrics['total_processing_time'] / total_tasks
            )
            
            self.logger.error(f"Task failed after {duration:.2f}s: {e}")
            raise
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance metrics report"""
        metrics = self.performance_metrics.copy()
        
        # Calculate success rate
        if metrics['tasks_processed'] > 0:
            metrics['success_rate'] = metrics['tasks_successful'] / metrics['tasks_processed']
        else:
            metrics['success_rate'] = 0.0
        
        # Add agent identification
        metrics['agent_id'] = getattr(self, 'agent_id', 'unknown')
        metrics['agent_name'] = getattr(self, 'name', 'unknown')
        
        return metrics


class ValidationMixin:
    """Mixin for input validation and security checks"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = getattr(self, 'logger', logging.getLogger(f"{__name__}.{getattr(self, 'agent_id', 'unknown')}"))
    
    def validate_task_content(self, content: str, max_length: int = 10000) -> str:
        """Validate and sanitize task content"""
        if not content or not isinstance(content, str):
            raise ValidationException("Task content must be a non-empty string")
        
        if len(content) > max_length:
            raise ValidationException(f"Task content too long: {len(content)} > {max_length}")
        
        # Basic sanitization
        content = content.strip()
        
        # Remove potentially dangerous patterns (basic security)
        dangerous_patterns = [
            r'rm\s+-rf\s+/',
            r'sudo\s+rm',
            r'>\s*/dev/null',
            r'curl.*\|\s*sh',
            r'wget.*\|\s*sh'
        ]
        
        import re
        for pattern in dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                self.logger.warning(f"Potentially dangerous pattern detected in task: {pattern}")
                # Don't reject, but log for monitoring
        
        return content
    
    def validate_file_path(self, file_path: str, allowed_extensions: List[str] = None) -> str:
        """Validate file path for security"""
        if not file_path or not isinstance(file_path, str):
            raise ValidationException("File path must be a non-empty string")
        
        # Prevent path traversal
        if '..' in file_path or file_path.startswith('/'):
            raise ValidationException("Invalid file path: path traversal detected")
        
        # Check extension if specified
        if allowed_extensions:
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in allowed_extensions:
                raise ValidationException(f"File extension {file_ext} not allowed")
        
        return file_path
    
    def validate_model_name(self, model_name: str) -> str:
        """Validate model name"""
        if not model_name or not isinstance(model_name, str):
            raise ValidationException("Model name must be a non-empty string")
        
        # Basic validation - alphanumeric, dashes, colons, underscores
        import re
        if not re.match(r'^[a-zA-Z0-9:_-]+$', model_name):
            raise ValidationException("Invalid model name format")
        
        return model_name