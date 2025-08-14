"""
Structured logging configuration
"""
import logging
import sys
from datetime import datetime
from typing import Optional

from .config import settings

class ColoredFormatter(logging.Formatter):
    """Colored log formatter for console output"""

    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)

def setup_logging(
    level: Optional[str] = None,
    format_string: Optional[str] = None,
    colored: bool = True
) -> None:
    """Setup application logging"""

    log_level = level or settings.LOG_LEVEL
    log_format = format_string or settings.LOG_FORMAT

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Apply colored formatter if requested
    if colored:
        formatter = ColoredFormatter(log_format)
        for handler in logging.root.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setFormatter(formatter)

def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)

# Performance logging utilities
class PerformanceLogger:
    """Context manager for performance logging"""

    def __init__(self, logger: logging.Logger, operation: str):
        self.logger = logger
        self.operation = operation
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"🚀 Starting {self.operation}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = datetime.now() - self.start_time
            if exc_type is None:
                self.logger.info(f"✅ Completed {self.operation} in {duration}")
            else:
                self.logger.error(f"❌ Failed {self.operation} after {duration}: {exc_val}")

# Setup default logging
setup_logging()