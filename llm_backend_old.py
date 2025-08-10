"""
Enhanced LLM Backend Abstraction Layer
Supports multiple backends: Ollama, ZLUDA+llama.cpp, ROCm
Includes circuit breaker pattern, health monitoring, and fallback mechanisms
"""
import os
import json
import subprocess
import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Protocol
from dataclasses import dataclass, field
from enum import Enum
import logging

from exceptions import (
    BackendException, 
    BackendUnavailableException, 
    ModelNotFoundException,
    TimeoutException
)

logger = logging.getLogger(__name__)

class BackendStatus(Enum):
    """Backend health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed" 
    CIRCUIT_OPEN = "circuit_open"


@dataclass
class BackendMetrics:
    """Performance metrics for a backend"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    last_success: Optional[float] = None
    last_failure: Optional[float] = None
    circuit_failures: int = 0


@dataclass
class BackendHealth:
    """Health tracking for a backend"""
    status: BackendStatus = BackendStatus.HEALTHY
    metrics: BackendMetrics = field(default_factory=BackendMetrics)
    circuit_open_until: Optional[float] = None


@dataclass
class LLMResponse:
    """Standardized LLM response format"""
    content: str
    model: str
    backend: str
    response_time: float = 0.0
    metadata: Optional[Dict[str, Any]] = None

class LLMBackend(ABC):
    """Abstract base class for LLM backends"""
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], model: str = None, **kwargs) -> LLMResponse:
        """Send chat messages and get response"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if backend is available"""
        pass
    
    @abstractmethod
    def get_models(self) -> List[str]:
        """Get available models"""
        pass

class OllamaBackend(LLMBackend):
    """Original Ollama backend"""
    
    def __init__(self):
        self.backend_name = "ollama"
    
    async def chat(self, messages: List[Dict[str, str]], model: str = "llama3", **kwargs) -> LLMResponse:
        try:
            import ollama
            response = ollama.chat(
                model=model,
                messages=messages,
                **kwargs
            )
            
            return LLMResponse(
                content=response['message']['content'],
                model=model,
                backend=self.backend_name,
                metadata=response
            )
        except Exception as e:
            logger.error(f"Ollama backend error: {e}")
            raise
    
    def is_available(self) -> bool:
        try:
            import ollama
            ollama.list()
            return True
        except:
            return False
    
    def get_models(self) -> List[str]:
        try:
            import ollama
            models = ollama.list()
            return [model['name'] for model in models['models']]
        except:
            return []

class ZludaLlamaCppBackend(LLMBackend):
    """ZLUDA + llama.cpp backend for AMD GPUs"""
    
    def __init__(self, llama_cpp_path: str = "./llama.cpp", model_path: str = None):
        self.backend_name = "zluda_llamacpp"
        self.llama_cpp_path = llama_cpp_path
        self.model_path = model_path or os.getenv("ZLUDA_MODEL_PATH", "./models/")
        self.zluda_path = os.getenv("ZLUDA_PATH", "/opt/zluda")
        
    async def chat(self, messages: List[Dict[str, str]], model: str = "llama3", **kwargs) -> LLMResponse:
        try:
            # Convert messages to prompt format
            prompt = self._messages_to_prompt(messages)
            
            # Prepare ZLUDA environment
            env = os.environ.copy()
            env["LD_LIBRARY_PATH"] = f"{self.zluda_path}/lib:{env.get('LD_LIBRARY_PATH', '')}"
            env["CUDA_VISIBLE_DEVICES"] = "0"  # Use first AMD GPU via ZLUDA
            
            # Find model file
            model_file = self._find_model_file(model)
            if not model_file:
                raise FileNotFoundError(f"Model {model} not found in {self.model_path}")
            
            # Prepare llama.cpp command (use llama-cli instead of main)
            cmd = [
                f"{self.llama_cpp_path}/llama-cli",
                "-m", model_file,
                "-p", prompt,
                "-n", str(kwargs.get('max_tokens', 512)),
                "-t", str(kwargs.get('threads', 8)),
                "--temp", str(kwargs.get('temperature', 0.7)),
                "--gpu-layers", str(kwargs.get('gpu_layers', 35)),
                "--batch-size", str(kwargs.get('batch_size', 512))
            ]
            
            # Run with ZLUDA
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"llama.cpp error: {stderr.decode()}")
                raise RuntimeError(f"llama.cpp failed: {stderr.decode()}")
            
            # Parse output (remove prompt echo)
            response_text = stdout.decode().strip()
            if prompt in response_text:
                response_text = response_text.split(prompt, 1)[1].strip()
            
            return LLMResponse(
                content=response_text,
                model=model,
                backend=self.backend_name,
                metadata={"command": " ".join(cmd)}
            )
            
        except Exception as e:
            logger.error(f"ZLUDA backend error: {e}")
            raise
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert chat messages to llama.cpp prompt format"""
        prompt_parts = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            if role == 'system':
                prompt_parts.append(f"### System:\n{content}\n")
            elif role == 'user':
                prompt_parts.append(f"### Human:\n{content}\n")
            elif role == 'assistant':
                prompt_parts.append(f"### Assistant:\n{content}\n")
        
        prompt_parts.append("### Assistant:\n")
        return "\n".join(prompt_parts)
    
    def _find_model_file(self, model: str) -> Optional[str]:
        """Find model file in model directory"""
        # First try exact match
        direct_path = os.path.join(self.model_path, model)
        if os.path.exists(direct_path):
            return direct_path
        
        # Then try with extensions
        possible_extensions = ['.gguf', '.ggml', '.bin']
        possible_names = [model, f"{model}-q4_0", f"{model}-q8_0"]
        
        for name in possible_names:
            for ext in possible_extensions:
                full_path = os.path.join(self.model_path, f"{name}{ext}")
                if os.path.exists(full_path):
                    return full_path
        
        # Finally, try to find any file that contains the model name
        try:
            for file in os.listdir(self.model_path):
                if model.lower() in file.lower() and file.endswith(('.gguf', '.ggml', '.bin')):
                    return os.path.join(self.model_path, file)
        except:
            pass
            
        return None
    
    def is_available(self) -> bool:
        """Check if ZLUDA and llama.cpp are available"""
        try:
            # For testing, don't require ZLUDA if llama.cpp works
            llama_main = os.path.join(self.llama_cpp_path, "llama-cli")
            if not os.path.exists(llama_main):
                return False
            
            # Check if any models are available
            if not os.path.exists(self.model_path):
                return False
                
            return len(self.get_models()) > 0
            
        except Exception:
            return False
    
    def get_models(self) -> List[str]:
        """Get available GGUF/GGML models"""
        models = []
        if not os.path.exists(self.model_path):
            return models
            
        try:
            for file in os.listdir(self.model_path):
                if file.endswith(('.gguf', '.ggml', '.bin')):
                    # Extract model name (remove extension and quantization suffix)
                    model_name = file.split('.')[0]
                    model_name = model_name.split('-q')[0]  # Remove quantization suffix
                    if model_name not in models:
                        models.append(model_name)
            return models
        except Exception:
            return []

class ROCmBackend(LLMBackend):
    """ROCm native backend for AMD GPUs"""
    
    def __init__(self):
        self.backend_name = "rocm"
        self._model_cache = {}
    
    async def chat(self, messages: List[Dict[str, str]], model: str = "llama3", **kwargs) -> LLMResponse:
        try:
            # This would require transformers with ROCm support
            # Implementation placeholder for future development
            import torch
            from transformers import AutoTokenizer, AutoModelForCausalLM
            
            if not torch.cuda.is_available():
                raise RuntimeError("ROCm/CUDA not available")
            
            # Load model (with caching)
            if model not in self._model_cache:
                tokenizer = AutoTokenizer.from_pretrained(f"meta-llama/{model}")
                model_obj = AutoModelForCausalLM.from_pretrained(
                    f"meta-llama/{model}",
                    device_map="auto",
                    torch_dtype=torch.float16
                )
                self._model_cache[model] = (tokenizer, model_obj)
            
            tokenizer, model_obj = self._model_cache[model]
            
            # Convert messages to prompt
            prompt = self._messages_to_prompt(messages)
            
            # Generate response
            inputs = tokenizer(prompt, return_tensors="pt").to(model_obj.device)
            
            with torch.no_grad():
                outputs = model_obj.generate(
                    **inputs,
                    max_new_tokens=kwargs.get('max_tokens', 512),
                    do_sample=True,
                    temperature=kwargs.get('temperature', 0.7),
                    top_p=kwargs.get('top_p', 0.9),
                    pad_token_id=tokenizer.eos_token_id
                )
            
            response_text = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
            
            return LLMResponse(
                content=response_text.strip(),
                model=model,
                backend=self.backend_name,
                metadata={"device": str(model_obj.device)}
            )
            
        except Exception as e:
            logger.error(f"ROCm backend error: {e}")
            raise
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages to chat format"""
        prompt_parts = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            prompt_parts.append(f"<|im_start|>{role}\n{content}<|im_end|>")
        
        prompt_parts.append("<|im_start|>assistant\n")
        return "\n".join(prompt_parts)
    
    def is_available(self) -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except:
            return False
    
    def get_models(self) -> List[str]:
        # Return commonly available models
        return ["llama2-7b", "llama2-13b", "mistral-7b", "codellama-7b"]

class EnhancedLLMBackendManager:
    """Enhanced manager for multiple LLM backends with circuit breaker and health monitoring"""
    
    def __init__(self, config_path: str = None, circuit_breaker_threshold: int = 5, circuit_breaker_timeout: int = 60):
        self.backends: Dict[str, LLMBackend] = {}
        self.backend_health: Dict[str, BackendHealth] = {}
        self.default_backend: Optional[str] = None
        self.config_path = config_path or os.getenv("LLM_BACKEND_CONFIG", "./llm_backends.json")
        
        # Circuit breaker configuration
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_timeout = circuit_breaker_timeout
        
        # Initialize backends
        self._init_backends()
        self._load_config()
        
        # Initialize health tracking for all backends
        for backend_name in self.backends.keys():
            if backend_name not in self.backend_health:
                self.backend_health[backend_name] = BackendHealth()
    
    def _init_backends(self):
        """Initialize all available backends"""
        # Ollama backend
        self.backends['ollama'] = OllamaBackend()
        
        # ZLUDA backend
        self.backends['zluda'] = ZludaLlamaCppBackend()
        
        # ROCm backend
        self.backends['rocm'] = ROCmBackend()
        
        # Set default to first available backend
        for name, backend in self.backends.items():
            if backend.is_available():
                self.default_backend = name
                logger.info(f"Using {name} as default backend")
                break
        
        if not self.default_backend:
            logger.warning("No LLM backends available")
    
    def _load_config(self):
        """Load backend configuration"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.default_backend = config.get('default_backend', self.default_backend)
                    
                    # Update backend configurations
                    for backend_name, backend_config in config.get('backends', {}).items():
                        if backend_name in self.backends:
                            # Apply configuration to backend
                            backend = self.backends[backend_name]
                            for key, value in backend_config.items():
                                if hasattr(backend, key):
                                    setattr(backend, key, value)
                                    
            except Exception as e:
                logger.error(f"Error loading backend config: {e}")
    
    def save_config(self):
        """Save current configuration"""
        config = {
            'default_backend': self.default_backend,
            'backends': {
                'ollama': {
                    'enabled': True,
                    'description': 'Original Ollama backend'
                },
                'zluda': {
                    'enabled': True,
                    'description': 'ZLUDA + llama.cpp for AMD GPUs',
                    'llama_cpp_path': getattr(self.backends.get('zluda'), 'llama_cpp_path', './llama.cpp'),
                    'model_path': getattr(self.backends.get('zluda'), 'model_path', './models/'),
                    'zluda_path': getattr(self.backends.get('zluda'), 'zluda_path', '/opt/zluda')
                },
                'rocm': {
                    'enabled': False,
                    'description': 'ROCm native backend for AMD GPUs'
                }
            }
        }
        
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving backend config: {e}")
    
    def get_available_backends(self) -> Dict[str, bool]:
        """Get status of all backends"""
        return {name: backend.is_available() for name, backend in self.backends.items()}
    
    def get_models(self, backend: str = None) -> List[str]:
        """Get available models for backend"""
        backend_name = backend or self.default_backend
        if backend_name and backend_name in self.backends:
            return self.backends[backend_name].get_models()
        return []
    
    def set_default_backend(self, backend: str):
        """Set default backend"""
        if backend in self.backends and self.backends[backend].is_available():
            self.default_backend = backend
            self.save_config()
        else:
            raise BackendUnavailableException(f"Backend {backend} not available")
    
    async def chat_with_fallback(self, 
                                messages: List[Dict[str, str]], 
                                model: str = None, 
                                backend: str = None, 
                                timeout: float = 120.0,
                                **kwargs) -> LLMResponse:
        """Chat with automatic fallback to other backends"""
        primary_backend = backend or self.default_backend
        
        # Try primary backend first
        if primary_backend and self._is_backend_available(primary_backend):
            try:
                return await asyncio.wait_for(
                    self._chat_with_metrics(primary_backend, messages, model, **kwargs),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                self._record_failure(primary_backend, TimeoutException(f"Request timed out after {timeout}s"))
                logger.warning(f"Primary backend {primary_backend} timed out")
            except Exception as e:
                self._record_failure(primary_backend, e)
                logger.warning(f"Primary backend {primary_backend} failed: {e}")
        
        # Try fallback backends sorted by health/priority
        fallback_candidates = self._get_fallback_candidates(exclude=primary_backend)
        
        for fallback_name in fallback_candidates:
            if self._is_backend_available(fallback_name):
                try:
                    logger.info(f"Trying fallback backend: {fallback_name}")
                    return await asyncio.wait_for(
                        self._chat_with_metrics(fallback_name, messages, model, **kwargs),
                        timeout=timeout
                    )
                except asyncio.TimeoutError:
                    self._record_failure(fallback_name, TimeoutException(f"Request timed out after {timeout}s"))
                    continue
                except Exception as e:
                    self._record_failure(fallback_name, e)
                    continue
                    
        raise BackendUnavailableException("All backends failed or are unavailable")

    async def _chat_with_metrics(self, 
                                backend_name: str, 
                                messages: List[Dict[str, str]], 
                                model: str, 
                                **kwargs) -> LLMResponse:
        """Execute chat request with performance metrics tracking"""
        start_time = time.time()
        health = self.backend_health[backend_name]
        
        try:
            backend = self.backends[backend_name]
            response = await backend.chat(messages, model, **kwargs)
            
            # Record success metrics
            duration = time.time() - start_time
            response.response_time = duration
            
            health.metrics.total_requests += 1
            health.metrics.successful_requests += 1
            health.metrics.last_success = time.time()
            
            # Update average response time
            total_successful = health.metrics.successful_requests
            current_avg = health.metrics.avg_response_time
            health.metrics.avg_response_time = (
                (current_avg * (total_successful - 1) + duration) / total_successful
            )
            
            # Reset circuit breaker on success
            if health.status == BackendStatus.CIRCUIT_OPEN:
                health.status = BackendStatus.HEALTHY
                health.circuit_open_until = None
                health.metrics.circuit_failures = 0
                logger.info(f"Circuit breaker closed for {backend_name}")
            
            return response
            
        except Exception as e:
            self._record_failure(backend_name, e)
            raise

    def _record_failure(self, backend_name: str, error: Exception):
        """Record backend failure and update circuit breaker"""
        health = self.backend_health[backend_name]
        health.metrics.total_requests += 1
        health.metrics.failed_requests += 1
        health.metrics.last_failure = time.time()
        health.metrics.circuit_failures += 1
        
        logger.error(f"Backend {backend_name} failed: {error}")
        
        # Check if circuit breaker should open
        if health.metrics.circuit_failures >= self.circuit_breaker_threshold:
            health.status = BackendStatus.CIRCUIT_OPEN
            health.circuit_open_until = time.time() + self.circuit_breaker_timeout
            logger.warning(f"Circuit breaker opened for {backend_name} after {health.metrics.circuit_failures} consecutive failures")

    def _is_backend_available(self, backend_name: str) -> bool:
        """Check if backend is available (not in circuit breaker state)"""
        if backend_name not in self.backend_health:
            return False
            
        health = self.backend_health[backend_name]
        
        # Check if circuit breaker is open and should be reset
        if health.status == BackendStatus.CIRCUIT_OPEN:
            if health.circuit_open_until and time.time() > health.circuit_open_until:
                health.status = BackendStatus.DEGRADED  # Half-open state
                health.metrics.circuit_failures = 0  # Reset failure count for testing
                logger.info(f"Circuit breaker half-open for {backend_name}")
                return True
            return False
            
        return backend_name in self.backends and self.backends[backend_name].is_available()

    def _get_fallback_candidates(self, exclude: Optional[str] = None) -> List[str]:
        """Get ordered list of fallback backend candidates"""
        candidates = []
        
        for name, health in self.backend_health.items():
            if name == exclude:
                continue
                
            # Calculate health score (higher is better)
            metrics = health.metrics
            if metrics.total_requests == 0:
                success_rate = 1.0  # New backend, give it a chance
            else:
                success_rate = metrics.successful_requests / metrics.total_requests
            
            # Factor in response time (lower is better)
            response_time_factor = 1.0 / (1.0 + metrics.avg_response_time)
            
            health_score = success_rate * response_time_factor
            candidates.append((name, health_score))
        
        # Sort by health score (descending) and return names
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [name for name, _ in candidates]

    def get_backend_health_report(self) -> Dict[str, Dict[str, Any]]:
        """Get comprehensive health report for all backends"""
        report = {}
        for name, health in self.backend_health.items():
            success_rate = 0.0
            if health.metrics.total_requests > 0:
                success_rate = health.metrics.successful_requests / health.metrics.total_requests
                
            report[name] = {
                "status": health.status.value,
                "success_rate": success_rate,
                "avg_response_time": health.metrics.avg_response_time,
                "total_requests": health.metrics.total_requests,
                "successful_requests": health.metrics.successful_requests,
                "failed_requests": health.metrics.failed_requests,
                "circuit_failures": health.metrics.circuit_failures,
                "last_success": health.metrics.last_success,
                "last_failure": health.metrics.last_failure,
                "circuit_open_until": health.circuit_open_until
            }
        return report

    async def health_check(self, backend_name: Optional[str] = None) -> Dict[str, bool]:
        """Perform health check on backends"""
        backends_to_check = [backend_name] if backend_name else list(self.backends.keys())
        health_status = {}
        
        for name in backends_to_check:
            if name in self.backends:
                try:
                    # Simple availability check
                    is_healthy = self.backends[name].is_available()
                    health_status[name] = is_healthy
                    
                    # Update health status
                    if name in self.backend_health:
                        if is_healthy and self.backend_health[name].status == BackendStatus.FAILED:
                            self.backend_health[name].status = BackendStatus.HEALTHY
                        elif not is_healthy and self.backend_health[name].status == BackendStatus.HEALTHY:
                            self.backend_health[name].status = BackendStatus.FAILED
                            
                except Exception as e:
                    logger.error(f"Health check failed for {name}: {e}")
                    health_status[name] = False
                    if name in self.backend_health:
                        self.backend_health[name].status = BackendStatus.FAILED
            else:
                health_status[name] = False
        
        return health_status

# Keep original class for backward compatibility
class LLMBackendManager(EnhancedLLMBackendManager):
    """Legacy backend manager for backward compatibility"""
    
    def __init__(self, config_path: str = None):
        super().__init__(config_path)
        
    async def chat(self, messages: List[Dict[str, str]], model: str = None, backend: str = None, **kwargs) -> LLMResponse:
        """Legacy chat method for backward compatibility"""
        return await self.chat_with_fallback(messages, model, backend, **kwargs)
    
    def _init_backends(self):
        """Initialize all available backends"""
        # Ollama backend
        self.backends['ollama'] = OllamaBackend()
        
        # ZLUDA backend
        self.backends['zluda'] = ZludaLlamaCppBackend()
        
        # ROCm backend
        self.backends['rocm'] = ROCmBackend()
        
        # Set default to first available backend
        for name, backend in self.backends.items():
            if backend.is_available():
                self.default_backend = name
                logger.info(f"Using {name} as default backend")
                break
        
        if not self.default_backend:
            logger.warning("No LLM backends available")
    
    def _load_config(self):
        """Load backend configuration"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.default_backend = config.get('default_backend', self.default_backend)
                    
                    # Update backend configurations
                    for backend_name, backend_config in config.get('backends', {}).items():
                        if backend_name in self.backends:
                            # Apply configuration to backend
                            backend = self.backends[backend_name]
                            for key, value in backend_config.items():
                                if hasattr(backend, key):
                                    setattr(backend, key, value)
                                    
            except Exception as e:
                logger.error(f"Error loading backend config: {e}")
    
    def save_config(self):
        """Save current configuration"""
        config = {
            'default_backend': self.default_backend,
            'backends': {
                'zluda': {
                    'llama_cpp_path': getattr(self.backends.get('zluda'), 'llama_cpp_path', './llama.cpp'),
                    'model_path': getattr(self.backends.get('zluda'), 'model_path', './models/'),
                    'zluda_path': getattr(self.backends.get('zluda'), 'zluda_path', '/opt/zluda')
                }
            }
        }
        
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving backend config: {e}")
    
    async def chat(self, messages: List[Dict[str, str]], model: str = None, backend: str = None, **kwargs) -> LLMResponse:
        """Send chat request using specified or default backend"""
        backend_name = backend or self.default_backend
        
        if not backend_name or backend_name not in self.backends:
            raise ValueError(f"Backend {backend_name} not available")
        
        backend_obj = self.backends[backend_name]
        if not backend_obj.is_available():
            raise RuntimeError(f"Backend {backend_name} is not available")
        
        return await backend_obj.chat(messages, model, **kwargs)
    
    def get_available_backends(self) -> Dict[str, bool]:
        """Get status of all backends"""
        return {name: backend.is_available() for name, backend in self.backends.items()}
    
    def get_models(self, backend: str = None) -> List[str]:
        """Get available models for backend"""
        backend_name = backend or self.default_backend
        if backend_name and backend_name in self.backends:
            return self.backends[backend_name].get_models()
        return []
    
    def set_default_backend(self, backend: str):
        """Set default backend"""
        if backend in self.backends and self.backends[backend].is_available():
            self.default_backend = backend
            self.save_config()
        else:
            raise ValueError(f"Backend {backend} not available")

# Global backend manager instance
backend_manager = LLMBackendManager()

# Convenience functions for backward compatibility
async def chat(messages: List[Dict[str, str]], model: str = "llama3", **kwargs) -> LLMResponse:
    """Convenience function for chat requests"""
    return await backend_manager.chat(messages, model, **kwargs)

def get_available_backends() -> Dict[str, bool]:
    """Get available backends"""
    return backend_manager.get_available_backends()

def set_backend(backend: str):
    """Set default backend"""
    backend_manager.set_default_backend(backend)