"""
Centralized exception handling for Ollama Flow framework
"""
from typing import Any, Optional


class OllamaFlowException(Exception):
    """Base exception for Ollama Flow framework"""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.details = details
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message


class BackendException(OllamaFlowException):
    """Backend-related exceptions"""
    pass


class BackendUnavailableException(BackendException):
    """Backend is not available or configured incorrectly"""
    pass


class ModelNotFoundException(BackendException):
    """Requested model is not found or not available"""
    pass


class AgentException(OllamaFlowException):
    """Agent-related exceptions"""
    pass


class TaskDecompositionException(AgentException):
    """Task decomposition failures"""
    pass


class AgentCommunicationException(AgentException):
    """Agent communication failures"""
    pass


class DatabaseException(OllamaFlowException):
    """Database operation exceptions"""
    pass


class ConfigurationException(OllamaFlowException):
    """Configuration-related exceptions"""
    pass


class ValidationException(OllamaFlowException):
    """Input validation exceptions"""
    pass


class TimeoutException(OllamaFlowException):
    """Operation timeout exceptions"""
    pass


class SecurityException(OllamaFlowException):
    """Security-related exceptions"""
    pass