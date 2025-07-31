"""
TechInsights  - Logging Configuration
Structured logging setup with JSON formatting
"""

import logging
import sys
from typing import Any, Dict
from pythonjsonlogger import jsonlogger
import structlog

from src.core.config import settings


def setup_logging() -> None:
    """
    Configure structured logging for the application.
    
    Sets up JSON logging for production and human-readable logging for development.
    """
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.is_production else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Remove default handlers
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    if settings.is_production:
        # JSON formatter for production
        formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(name)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        # Human-readable formatter for development
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    configure_loggers()
    
    # Log configuration
    logger = structlog.get_logger(__name__)
    logger.info(
        "Logging configured",
        environment=settings.ENVIRONMENT,
        log_level=settings.LOG_LEVEL,
        format="json" if settings.is_production else "console"
    )


def configure_loggers() -> None:
    """Configure specific loggers with appropriate levels."""
    
    # Set levels for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DATABASE_ECHO else logging.WARNING
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    
    # Set debug level for our application in development
    if settings.is_development:
        logging.getLogger("src").setLevel(logging.DEBUG)


class ContextLogger:
    """
    Context-aware logger that adds request context to log messages.
    """
    
    def __init__(self, name: str):
        self.logger = structlog.get_logger(name)
        self._context: Dict[str, Any] = {}
    
    def bind(self, **kwargs) -> 'ContextLogger':
        """Bind context variables to the logger."""
        new_logger = ContextLogger(self.logger.name)
        new_logger._context = {**self._context, **kwargs}
        new_logger.logger = self.logger.bind(**new_logger._context)
        return new_logger
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message with context."""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message with context."""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message with context."""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message with context."""
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message with context."""
        self.logger.critical(message, **kwargs)


def get_logger(name: str) -> ContextLogger:
    """
    Get a context-aware logger instance.
    
    Args:
        name: Logger name
    
    Returns:
        ContextLogger: Context-aware logger instance
    """
    return ContextLogger(name)