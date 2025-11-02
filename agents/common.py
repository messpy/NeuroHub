#!/usr/bin/env python3
"""Common agent base classes and utilities.

This module provides shared functionality for all NeuroHub agents:
- BaseAgent class with common methods
- Logging setup
- Error handling patterns
- Configuration loading
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import yaml


class BaseAgent:
    """Base class for all NeuroHub agents.

    Provides common functionality:
    - Logging setup
    - Configuration management
    - Error handling
    """

    def __init__(self, name: str, config_path: Optional[Path] = None):
        """Initialize base agent.

        Args:
            name: Agent name for logging
            config_path: Path to config file. Defaults to config/agent_config.yaml
        """
        self.name = name
        self.logger = self._setup_logging()

        # Load configuration
        if config_path is None:
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "agent_config.yaml"

        self.config = self._load_config(config_path)

        self.logger.info(f"{self.name} agent initialized")

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the agent.

        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(self.name)

        # Avoid duplicate handlers
        if logger.handlers:
            return logger

        logger.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

        # File handler (optional)
        project_root = Path(__file__).parent.parent
        logs_dir = project_root / "logs"
        logs_dir.mkdir(exist_ok=True)

        file_handler = logging.FileHandler(
            logs_dir / f"{self.name}.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from YAML file.

        Args:
            config_path: Path to config file

        Returns:
            Configuration dictionary
        """
        if not config_path.exists():
            self.logger.warning(f"Config file not found: {config_path}")
            return {}

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # Get agent-specific config
            agent_config = config.get(self.name, {})

            self.logger.debug(f"Loaded config for {self.name}")
            return agent_config

        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return {}

    def handle_error(self, error: Exception, context: str = "") -> None:
        """Handle errors with logging.

        Args:
            error: Exception that occurred
            context: Context information
        """
        error_msg = f"{context}: {str(error)}" if context else str(error)
        self.logger.error(error_msg, exc_info=True)

    def validate_input(self, data: Any, required_fields: list) -> bool:
        """Validate input data.

        Args:
            data: Input data (usually dict)
            required_fields: List of required field names

        Returns:
            True if valid
        """
        if not isinstance(data, dict):
            self.logger.error("Input must be a dictionary")
            return False

        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            self.logger.error(f"Missing required fields: {missing_fields}")
            return False

        return True

    def execute(self, *args, **kwargs) -> Any:
        """Execute agent's main functionality.

        Must be implemented by subclasses.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Agent-specific result

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError(f"{self.name} agent must implement execute() method")


def setup_agent_logging(agent_name: str, log_level: str = "INFO") -> logging.Logger:
    """Setup logging for an agent.

    Utility function for quick logging setup without BaseAgent.

    Args:
        agent_name: Name of the agent
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger
    """
    logger = logging.getLogger(agent_name)

    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, log_level.upper()))

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def load_agent_config(agent_name: str, config_file: str = "agent_config.yaml") -> Dict[str, Any]:
    """Load agent configuration.

    Utility function for loading config without BaseAgent.

    Args:
        agent_name: Name of the agent
        config_file: Config filename in config/ directory

    Returns:
        Agent configuration dictionary
    """
    project_root = Path(__file__).parent.parent
    config_path = project_root / "config" / config_file

    if not config_path.exists():
        return {}

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config.get(agent_name, {})
    except Exception:
        return {}


class AgentError(Exception):
    """Base exception for agent errors."""
    pass


class AgentConfigError(AgentError):
    """Configuration error."""
    pass


class AgentExecutionError(AgentError):
    """Execution error."""
    pass


class AgentValidationError(AgentError):
    """Validation error."""
    pass


def main():
    """CLI entry point for testing."""
    import argparse

    parser = argparse.ArgumentParser(description='Test agent common functionality')
    parser.add_argument('--test', action='store_true', help='Run test')

    args = parser.parse_args()

    if args.test:
        # Test BaseAgent
        class TestAgent(BaseAgent):
            def execute(self, message: str) -> str:
                self.logger.info(f"Executing with message: {message}")
                return f"Processed: {message}"

        agent = TestAgent("test_agent")
        result = agent.execute("Hello, NeuroHub!")
        print(result)

        # Test validation
        valid = agent.validate_input(
            {"name": "test", "value": 123},
            ["name", "value"]
        )
        print(f"Validation result: {valid}")


if __name__ == '__main__':
    main()
