#!/usr/bin/env python3
"""
Unified Configuration Management for Ollama Flow
Pydantic-based configuration with environment support and validation
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml
import os
from enum import Enum

class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"

class DatabaseConfig(BaseSettings):
    """Database configuration settings"""
    url: str = Field(default="sqlite:///ollama_flow.db", description="Database URL")
    pool_size: int = Field(default=10, description="Connection pool size")
    max_overflow: int = Field(default=20, description="Max connection overflow")
    echo: bool = Field(default=False, description="Echo SQL queries")
    
class LLMConfig(BaseSettings):
    """LLM configuration settings"""
    default_model: str = Field(default="llama3", description="Default LLM model")
    max_model_size_gb: float = Field(default=5.5, description="Maximum model size in GB")
    request_timeout: int = Field(default=300, description="Request timeout in seconds")
    max_concurrent_requests: int = Field(default=5, description="Max concurrent LLM requests")
    enable_caching: bool = Field(default=True, description="Enable response caching")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    
    # Role-specific model mappings
    role_mappings: Dict[str, Dict[str, Any]] = Field(
        default={
            "developer": {"primary": "codellama:7b", "fallback": ["llama3", "phi3:mini"]},
            "security_specialist": {"primary": "llama3", "fallback": ["codellama:7b", "phi3:medium"]},
            "analyst": {"primary": "llama3", "fallback": ["phi3:medium", "codellama:7b"]},
            "datascientist": {"primary": "codellama:7b", "fallback": ["llama3", "phi3:medium"]},
            "it_architect": {"primary": "llama3", "fallback": ["codellama:7b", "phi3:medium"]}
        }
    )

class AgentConfig(BaseSettings):
    """Agent system configuration"""
    max_agents: int = Field(default=10, description="Maximum number of concurrent agents")
    default_timeout: int = Field(default=300, description="Default agent timeout")
    enable_command_execution: bool = Field(default=True, description="Allow command execution")
    enable_code_generation: bool = Field(default=True, description="Allow code generation")
    project_folder: Optional[str] = Field(default=None, description="Default project folder")
    
    # Role assignment settings
    role_assignment_algorithm: str = Field(default="weighted_keywords", description="Role assignment method")
    enable_dynamic_roles: bool = Field(default=True, description="Enable dynamic role assignment")

class PerformanceConfig(BaseSettings):
    """Performance and optimization settings"""
    enable_async_db: bool = Field(default=True, description="Use async database operations")
    database_poll_interval: float = Field(default=1.0, description="Database polling interval (seconds)")
    enable_request_batching: bool = Field(default=True, description="Enable LLM request batching")
    batch_size: int = Field(default=5, description="Request batch size")
    enable_monitoring: bool = Field(default=True, description="Enable performance monitoring")

class SecurityConfig(BaseSettings):
    """Security configuration settings"""
    enable_command_whitelist: bool = Field(default=True, description="Enable command whitelist")
    allowed_commands: List[str] = Field(
        default=["ls", "cat", "grep", "find", "python", "pip", "git"],
        description="Allowed shell commands"
    )
    max_command_timeout: int = Field(default=60, description="Max command execution timeout")
    enable_file_restrictions: bool = Field(default=True, description="Enable file access restrictions")
    allowed_file_extensions: List[str] = Field(
        default=[".py", ".js", ".ts", ".json", ".yaml", ".yml", ".md", ".txt"],
        description="Allowed file extensions for operations"
    )

class LoggingConfig(BaseSettings):
    """Logging configuration"""
    level: str = Field(default="INFO", description="Log level")
    format: str = Field(default="json", description="Log format (json or text)")
    file: Optional[str] = Field(default="ollama_flow.log", description="Log file path")
    max_file_size: str = Field(default="10MB", description="Max log file size")
    backup_count: int = Field(default=5, description="Number of backup log files")
    enable_correlation_ids: bool = Field(default=True, description="Enable correlation ID tracking")

class OllamaFlowSettings(BaseSettings):
    """Main application settings"""
    
    # Environment
    environment: Environment = Field(default=Environment.DEVELOPMENT, description="Runtime environment")
    debug: bool = Field(default=False, description="Debug mode")
    version: str = Field(default="2.0.0", description="Application version")
    
    # Core configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    agents: AgentConfig = Field(default_factory=AgentConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    # Paths
    config_dir: Path = Field(default=Path("config"), description="Configuration directory")
    data_dir: Path = Field(default=Path("data"), description="Data directory")
    logs_dir: Path = Field(default=Path("logs"), description="Logs directory")
    
    @field_validator('config_dir', 'data_dir', 'logs_dir')
    def ensure_paths_exist(cls, v):
        """Ensure directories exist"""
        if isinstance(v, str):
            v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @field_validator('environment', mode='before')
    def parse_environment(cls, v):
        """Parse environment from string"""
        if isinstance(v, str):
            return Environment(v.lower())
        return v
    
    class Config:
        env_file = ".env"
        env_prefix = "OLLAMA_FLOW_"
        case_sensitive = False
        
    def load_environment_config(self) -> None:
        """Load environment-specific configuration"""
        config_file = self.config_dir / f"{self.environment.value}.yaml"
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                env_config = yaml.safe_load(f)
                
            # Update configurations with environment-specific values
            for key, value in env_config.items():
                if hasattr(self, key):
                    if isinstance(value, dict) and hasattr(getattr(self, key), '__dict__'):
                        # Update nested configuration objects
                        for nested_key, nested_value in value.items():
                            setattr(getattr(self, key), nested_key, nested_value)
                    else:
                        setattr(self, key, value)
    
    def save_current_config(self, filepath: Optional[Path] = None) -> None:
        """Save current configuration to file"""
        if filepath is None:
            filepath = self.config_dir / f"current_{self.environment.value}.yaml"
        
        config_dict = {}
        for field_name, field_info in self.model_fields.items():
            value = getattr(self, field_name)
            if hasattr(value, 'model_dump'):
                config_dict[field_name] = value.model_dump()
            else:
                config_dict[field_name] = value
        
        with open(filepath, 'w') as f:
            yaml.safe_dump(config_dict, f, default_flow_style=False, indent=2)

# Global settings instance
_settings: Optional[OllamaFlowSettings] = None

def get_settings() -> OllamaFlowSettings:
    """Get global settings instance"""
    global _settings
    if _settings is None:
        _settings = OllamaFlowSettings()
        _settings.load_environment_config()
    return _settings

def reload_settings() -> OllamaFlowSettings:
    """Reload settings from configuration"""
    global _settings
    _settings = None
    return get_settings()

def create_default_configs() -> None:
    """Create default configuration files for all environments"""
    base_config = {
        'database': {
            'url': 'sqlite:///data/ollama_flow.db',
            'pool_size': 10,
            'echo': False
        },
        'llm': {
            'default_model': 'llama3',
            'max_model_size_gb': 5.5,
            'request_timeout': 300,
            'enable_caching': True
        },
        'agents': {
            'max_agents': 10,
            'enable_command_execution': True,
            'enable_code_generation': True
        },
        'performance': {
            'enable_async_db': True,
            'database_poll_interval': 1.0,
            'enable_request_batching': True
        },
        'security': {
            'enable_command_whitelist': True,
            'max_command_timeout': 60
        },
        'logging': {
            'level': 'INFO',
            'format': 'json',
            'file': 'logs/ollama_flow.log'
        }
    }
    
    environments = {
        'development': {
            **base_config,
            'database': {'url': 'sqlite:///data/dev_ollama_flow.db', 'echo': True},
            'logging': {'level': 'DEBUG'},
            'debug': True
        },
        'testing': {
            **base_config,
            'database': {'url': 'sqlite:///:memory:', 'echo': False},
            'logging': {'level': 'WARNING'},
            'performance': {'database_poll_interval': 0.1}
        },
        'production': {
            **base_config,
            'database': {'url': 'sqlite:///data/prod_ollama_flow.db', 'echo': False},
            'logging': {'level': 'INFO', 'file': 'logs/prod_ollama_flow.log'},
            'security': {'enable_command_whitelist': True, 'enable_file_restrictions': True},
            'debug': False
        }
    }
    
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    for env_name, env_config in environments.items():
        config_file = config_dir / f"{env_name}.yaml"
        with open(config_file, 'w') as f:
            yaml.safe_dump(env_config, f, default_flow_style=False, indent=2)
        print(f"✅ Created {env_name} configuration: {config_file}")

if __name__ == "__main__":
    # Create default configuration files
    create_default_configs()
    
    # Test configuration loading
    settings = get_settings()
    print(f"🔧 Configuration loaded for {settings.environment} environment")
    print(f"📊 Database: {settings.database.url}")
    print(f"🤖 Default LLM: {settings.llm.default_model}")
    print(f"👥 Max agents: {settings.agents.max_agents}")
    
    # Save current config for reference
    settings.save_current_config()
    print(f"💾 Current configuration saved to config/current_{settings.environment.value}.yaml")