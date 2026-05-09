"""
Logging configuration for the AutoAttendance system.
Provides structured logging with file and console output.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime

# Application name
APP_NAME = "AutoAttendance"
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Log file path with rotation
LOG_FILE = LOG_DIR / f"attendance_{datetime.now().strftime('%Y%m')}.log"

# Define log format
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Maximum log file size: 10MB
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5


def setup_logger(name: str = APP_NAME, level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return a logger instance.
    
    Args:
        name: Logger name (typically module name)
        level: Logging level (default: INFO)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler with color support
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(
        logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    )
    logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(
        logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    )
    logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = APP_NAME) -> logging.Logger:
    """
    Get an existing logger or create a new one.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger


# Application logger instance
app_logger = setup_logger()


def log_system_event(event_type: str, message: str, **kwargs) -> None:
    """
    Log a system event with structured data.
    
    Args:
        event_type: Type of event (INFO, WARNING, ERROR, etc.)
        message: Event message
        **kwargs: Additional event data
    """
    logger = get_logger()
    extra_data = " | ".join(f"{k}={v}" for k, v in kwargs.items() if v is not None)
    full_message = f"{message} | {extra_data}" if extra_data else message
    
    getattr(logger, event_type.lower())(full_message)