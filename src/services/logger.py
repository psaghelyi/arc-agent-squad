"""
Logging configuration for the Voice Agent Swarm application.

This module sets up structured logging using structlog.
"""

import logging
import sys
from typing import Any, Dict

import structlog
from structlog.typing import FilteringBoundLogger


def setup_logging(log_level: str = "INFO", renderer: str = "json") -> None:
    """
    Set up structured logging for the application.
    
    Args:
        log_level: The log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        renderer: The log renderer type ('json' or 'console')
    """
    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    if renderer == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )


def get_logger(name: str) -> FilteringBoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: The logger name (typically __name__)
        
    Returns:
        A structured logger instance
    """
    return structlog.get_logger(name)


class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""
    
    @property
    def logger(self) -> FilteringBoundLogger:
        """Get a logger instance for this class."""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger 