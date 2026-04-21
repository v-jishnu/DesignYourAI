"""
Base agent class for all agents in the MCQ ingestion system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
import logging


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize base agent.

        Args:
            name: Agent name for logging
            config: Configuration dictionary
        """
        self.name = name
        self.config = config
        self.logger = logging.getLogger(name)

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """
        Main execution method to be implemented by subclasses.

        Returns:
            Result of agent execution
        """
        pass

    def log_action(self, message: str, level: str = 'info'):
        """
        Log an action with standardized format.

        Args:
            message: Message to log
            level: Log level (info, warning, error, debug)
        """
        log_func = getattr(self.logger, level.lower())
        log_func(f"[{self.name}] {message}")

    def handle_error(self, error: Exception, context: str):
        """
        Handle errors with logging.

        Args:
            error: Exception that occurred
            context: Context where error happened
        """
        from utils.logger import ErrorHandler
        ErrorHandler.log_error(self.logger, context, error)

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value with fallback.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)
