"""
Logging and error handling utilities.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import asyncio
from typing import Callable, Any, Type
from functools import wraps


def setup_logging(log_dir: Path, level: str = 'INFO'):
    """
    Configure logging with file and console handlers.

    Args:
        log_dir: Directory for log files
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    log_dir.mkdir(exist_ok=True, parents=True)
    log_file = log_dir / 'app.log'

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler with rotation (10MB max, 5 backups)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return root_logger


class RetryHandler:
    """Retry logic for handling transient failures."""

    @staticmethod
    async def retry_with_backoff(
        func: Callable,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        exceptions: tuple = (Exception,)
    ) -> Any:
        """
        Retry a function with exponential backoff.

        Args:
            func: Async function to retry
            max_retries: Maximum number of retry attempts
            backoff_factor: Multiplier for wait time between retries
            exceptions: Tuple of exceptions to catch and retry

        Returns:
            Result of successful function execution

        Raises:
            Last exception if all retries fail
        """
        logger = logging.getLogger(__name__)

        for attempt in range(max_retries):
            try:
                return await func()
            except exceptions as e:
                if attempt == max_retries - 1:
                    logger.error(f"All {max_retries} retry attempts failed: {e}")
                    raise

                wait_time = backoff_factor ** attempt
                logger.warning(
                    f"Retry {attempt + 1}/{max_retries} after {wait_time}s due to: {e}"
                )
                await asyncio.sleep(wait_time)

    @staticmethod
    def retry_sync(
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        exceptions: tuple = (Exception,)
    ):
        """
        Decorator for synchronous retry with exponential backoff.

        Args:
            max_retries: Maximum number of retry attempts
            backoff_factor: Multiplier for wait time between retries
            exceptions: Tuple of exceptions to catch and retry
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                logger = logging.getLogger(func.__module__)

                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        if attempt == max_retries - 1:
                            logger.error(f"All {max_retries} retry attempts failed: {e}")
                            raise

                        import time
                        wait_time = backoff_factor ** attempt
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} after {wait_time}s due to: {e}"
                        )
                        time.sleep(wait_time)

            return wrapper
        return decorator


class ErrorHandler:
    """Centralized error handling."""

    @staticmethod
    def log_error(logger: logging.Logger, context: str, error: Exception):
        """
        Log an error with context.

        Args:
            logger: Logger instance
            context: Context where error occurred
            error: Exception that was raised
        """
        logger.error(f"Error in {context}: {type(error).__name__}: {str(error)}")

    @staticmethod
    def should_skip(error: Exception) -> bool:
        """
        Determine if an error should cause skipping rather than failing.

        Args:
            error: Exception to evaluate

        Returns:
            True if should skip, False if should fail
        """
        # Extraction errors: skip source and continue
        skip_errors = (
            ConnectionError,
            TimeoutError,
            FileNotFoundError,
            PermissionError,
        )

        return isinstance(error, skip_errors)
