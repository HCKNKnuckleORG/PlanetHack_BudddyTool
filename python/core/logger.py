"""
Logging configuration for PlanetHack
Supports structured logging with different environments.
Errors are always written to logs/planethack_errors.log - check there first when debugging.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from loguru import logger as loguru_logger
from colorlog import ColoredFormatter

# Canonical error log path - check this first when something goes wrong
LOGS_DIR = Path("logs")
ERROR_LOG_PATH = LOGS_DIR / "planethack_errors.log"


class InterceptHandler(logging.Handler):
    """Intercept standard logging messages toward loguru"""
    def emit(self, record):
        try:
            level = loguru_logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        loguru_logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def setup_logger(level="INFO", env="dev", no_color=False):
    """Setup logger with appropriate configuration.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        env: Environment (dev, build, prod)
        no_color: If True, disable ANSI color output for terminals like Tilix
    """

    loguru_logger.remove()

    logs_dir = LOGS_DIR
    logs_dir.mkdir(exist_ok=True)

    # Errors-only sink: always written immediately, no rotation - check this first when debugging
    error_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}\n"
        "{exception}"
    )
    loguru_logger.add(
        str(ERROR_LOG_PATH),
        format=error_format,
        level="ERROR",
        rotation="1 day",
        retention="90 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
    )

    if no_color:
        format_string = (
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        )
    else:
        format_string = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )

    is_dev = (env == "dev")

    loguru_logger.add(
        sys.stdout,
        format=format_string,
        level=level,
        colorize=(not no_color),
        backtrace=is_dev,
        diagnose=is_dev,
    )

    log_file = logs_dir / f"planethack_{env}_{datetime.now().strftime('%Y%m%d')}.log"
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    )
    loguru_logger.add(
        log_file,
        format=file_format,
        level=level,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        backtrace=is_dev,
        diagnose=is_dev,
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    loguru_logger.info(f"Logging to {log_file}; errors also to {ERROR_LOG_PATH}")
    return loguru_logger
