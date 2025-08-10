"""
Centralized configuration management for Ollama Flow framework
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from pathlib import Path
import os
import json
import logging
from exceptions import ConfigurationException


@dataclass
class BackendConfig:
    """Configuration for a specific LLM backend"""
    name: str
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1  # Lower number = higher priority for fallback
    
    def __post_init__(self):
        if not self.name:
            raise ConfigurationException("Backend name cannot be empty")


@dataclass
class DatabaseConfig:
    """Database configuration"""
    path: str = "ollama_flow_messages.db"
    timeout: int = 30
    pool_size: int = 5
    cleanup_interval_hours: int = 24
    
    def __post_init__(self):
        if self.timeout <= 0:
            raise ConfigurationException("Database timeout must be positive")
        if self.pool_size <= 0:
            raise ConfigurationException("Database pool size must be positive")


@dataclass
class AgentConfig:
    """Agent system configuration"""
    default_model: str = "llama3"
    max_workers: int = 10
    task_timeout: int = 300
    polling_interval: float = 0.1
    max_subtasks: int = 10
    
    def __post_init__(self):
        if self.max_workers <= 0:
            raise ConfigurationException("Max workers must be positive")
        if self.task_timeout <= 0:
            raise ConfigurationException("Task timeout must be positive")
        if self.polling_interval <= 0:
            raise ConfigurationException("Polling interval must be positive")


@dataclass
class SecurityConfig:
    """Security configuration"""
    enable_sandboxing: bool = True
    allowed_file_extensions: List[str] = field(default_factory=lambda: ['.py', '.txt', '.md', '.json'])
    max_file_size_mb: int = 10
    max_output_length: int = 10000
    validate_commands: bool = True
    
    def __post_init__(self):
        if self.max_file_size_mb <= 0:
            raise ConfigurationException("Max file size must be positive")
        if self.max_output_length <= 0:
            raise ConfigurationException("Max output length must be positive")


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size_mb: int = 10
    backup_count: int = 5
    enable_structured_logging: bool = False
    
    def __post_init__(self):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.level.upper() not in valid_levels:
            raise ConfigurationException(f"Invalid log level: {self.level}")


@dataclass
class PerformanceConfig:
    """Performance and monitoring configuration"""
    enable_metrics: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    request_timeout: int = 120
    max_concurrent_requests: int = 10
    
    def __post_init__(self):
        if self.circuit_breaker_threshold <= 0:
            raise ConfigurationException("Circuit breaker threshold must be positive")
        if self.circuit_breaker_timeout <= 0:
            raise ConfigurationException("Circuit breaker timeout must be positive")


@dataclass
class OllamaFlowConfig:
    """Main configuration class for Ollama Flow framework"""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    agents: AgentConfig = field(default_factory=AgentConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    backends: Dict[str, BackendConfig] = field(default_factory=dict)
    
    # Runtime configuration
    project_root: Path = field(default_factory=lambda: Path.cwd())
    default_backend: str = "ollama"
    environment: str = "development"
    
    def __post_init__(self):
        # Validate project root
        if not self.project_root.exists():
            raise ConfigurationException(f"Project root does not exist: {self.project_root}")
        
        # Ensure default backend exists
        if self.default_backend not in self.backends:
            # Add default ollama backend if not configured
            self.backends[self.default_backend] = BackendConfig(
                name=self.default_backend,
                enabled=True,
                priority=1
            )
    
    @classmethod
    def from_env(cls) -> 'OllamaFlowConfig':
        """Load configuration from environment variables"""
        config = cls()
        
        # Database configuration
        config.database.path = os.getenv("OLLAMA_DB_PATH", config.database.path)
        config.database.timeout = int(os.getenv("OLLAMA_DB_TIMEOUT", config.database.timeout))
        
        # Agent configuration
        config.agents.default_model = os.getenv("OLLAMA_MODEL", config.agents.default_model)
        config.agents.max_workers = int(os.getenv("OLLAMA_WORKER_COUNT", config.agents.max_workers))
        config.agents.task_timeout = int(os.getenv("OLLAMA_TASK_TIMEOUT", config.agents.task_timeout))
        
        # Logging configuration
        config.logging.level = os.getenv("OLLAMA_LOG_LEVEL", config.logging.level)
        config.logging.file_path = os.getenv("OLLAMA_LOG_FILE", config.logging.file_path)
        
        # Security configuration
        config.security.enable_sandboxing = os.getenv("OLLAMA_SECURE_MODE", "true").lower() == "true"
        
        # Performance configuration
        config.performance.enable_metrics = os.getenv("OLLAMA_METRICS", "true").lower() == "true"
        
        # Runtime configuration
        config.default_backend = os.getenv("OLLAMA_BACKEND", config.default_backend)
        config.environment = os.getenv("ENVIRONMENT", config.environment)
        
        # Project folder
        project_folder = os.getenv("OLLAMA_PROJECT_FOLDER")
        if project_folder:
            config.project_root = Path(project_folder)
        
        return config
    
    @classmethod
    def from_file(cls, config_path: Path) -> 'OllamaFlowConfig':
        """Load configuration from JSON file"""
        if not config_path.exists():
            raise ConfigurationException(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path) as f:
                data = json.load(f)
            
            # Parse configuration sections
            config = cls()
            
            # Load database config
            if 'database' in data:
                db_data = data['database']
                config.database = DatabaseConfig(**db_data)
            
            # Load agent config
            if 'agents' in data:
                agent_data = data['agents']
                config.agents = AgentConfig(**agent_data)
            
            # Load security config
            if 'security' in data:
                security_data = data['security']
                config.security = SecurityConfig(**security_data)
            
            # Load logging config
            if 'logging' in data:
                logging_data = data['logging']
                config.logging = LoggingConfig(**logging_data)
            
            # Load performance config
            if 'performance' in data:
                perf_data = data['performance']
                config.performance = PerformanceConfig(**perf_data)
            
            # Load backend configurations
            if 'backends' in data:
                for name, backend_data in data['backends'].items():
                    config.backends[name] = BackendConfig(name=name, **backend_data)
            
            # Load runtime config
            config.default_backend = data.get('default_backend', config.default_backend)
            config.environment = data.get('environment', config.environment)
            
            if 'project_root' in data:
                config.project_root = Path(data['project_root'])
            
            return config
            
        except json.JSONDecodeError as e:
            raise ConfigurationException(f"Invalid JSON in config file: {e}")
        except Exception as e:
            raise ConfigurationException(f"Error loading configuration: {e}")
    
    def save_to_file(self, config_path: Path) -> None:
        """Save configuration to JSON file"""
        try:
            config_data = {
                'default_backend': self.default_backend,
                'environment': self.environment,
                'project_root': str(self.project_root),
                'database': {
                    'path': self.database.path,
                    'timeout': self.database.timeout,
                    'pool_size': self.database.pool_size,
                    'cleanup_interval_hours': self.database.cleanup_interval_hours
                },
                'agents': {
                    'default_model': self.agents.default_model,
                    'max_workers': self.agents.max_workers,
                    'task_timeout': self.agents.task_timeout,
                    'polling_interval': self.agents.polling_interval,
                    'max_subtasks': self.agents.max_subtasks
                },
                'security': {
                    'enable_sandboxing': self.security.enable_sandboxing,
                    'allowed_file_extensions': self.security.allowed_file_extensions,
                    'max_file_size_mb': self.security.max_file_size_mb,
                    'max_output_length': self.security.max_output_length,
                    'validate_commands': self.security.validate_commands
                },
                'logging': {
                    'level': self.logging.level,
                    'format': self.logging.format,
                    'file_path': self.logging.file_path,
                    'max_file_size_mb': self.logging.max_file_size_mb,
                    'backup_count': self.logging.backup_count,
                    'enable_structured_logging': self.logging.enable_structured_logging
                },
                'performance': {
                    'enable_metrics': self.performance.enable_metrics,
                    'circuit_breaker_threshold': self.performance.circuit_breaker_threshold,
                    'circuit_breaker_timeout': self.performance.circuit_breaker_timeout,
                    'request_timeout': self.performance.request_timeout,
                    'max_concurrent_requests': self.performance.max_concurrent_requests
                },
                'backends': {
                    name: {
                        'enabled': backend.enabled,
                        'config': backend.config,
                        'priority': backend.priority
                    }
                    for name, backend in self.backends.items()
                }
            }
            
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2, default=str)
                
        except Exception as e:
            raise ConfigurationException(f"Error saving configuration: {e}")
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Validate project root
        if not self.project_root.exists():
            issues.append(f"Project root does not exist: {self.project_root}")
        
        # Validate backend configuration
        if not self.backends:
            issues.append("No backends configured")
        
        if self.default_backend not in self.backends:
            issues.append(f"Default backend '{self.default_backend}' not found in configured backends")
        
        # Validate enabled backends
        enabled_backends = [name for name, backend in self.backends.items() if backend.enabled]
        if not enabled_backends:
            issues.append("No backends are enabled")
        
        return issues
    
    def get_sorted_backends(self) -> List[tuple[str, BackendConfig]]:
        """Get backends sorted by priority (lower number = higher priority)"""
        enabled_backends = [(name, backend) for name, backend in self.backends.items() if backend.enabled]
        return sorted(enabled_backends, key=lambda x: x[1].priority)


# Global configuration instance
_global_config: Optional[OllamaFlowConfig] = None


def get_config() -> OllamaFlowConfig:
    """Get the global configuration instance"""
    global _global_config
    if _global_config is None:
        _global_config = OllamaFlowConfig.from_env()
    return _global_config


def set_config(config: OllamaFlowConfig) -> None:
    """Set the global configuration instance"""
    global _global_config
    _global_config = config


def load_config_from_file(config_path: Path) -> OllamaFlowConfig:
    """Load configuration from file and set as global config"""
    config = OllamaFlowConfig.from_file(config_path)
    set_config(config)
    return config


def init_logging(config: Optional[LoggingConfig] = None) -> None:
    """Initialize logging based on configuration"""
    if config is None:
        config = get_config().logging
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, config.level.upper()),
        format=config.format
    )
    
    # Add file handler if specified
    if config.file_path:
        from logging.handlers import RotatingFileHandler
        
        file_handler = RotatingFileHandler(
            config.file_path,
            maxBytes=config.max_file_size_mb * 1024 * 1024,
            backupCount=config.backup_count
        )
        file_handler.setFormatter(logging.Formatter(config.format))
        
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)