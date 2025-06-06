"""Structured logging configuration with structlog."""
import logging
import sys
from typing import Any, Dict, Literal

import structlog
from structlog.types import EventDict, Processor


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add application context to log entries."""
    event_dict["app"] = "smart-devops-assistant"
    event_dict["version"] = "0.1.0"
    return event_dict


def setup_logging(
    level: str = "INFO",
    format_type: Literal["json", "console"] = "json",
    development: bool = False,
) -> None:
    """Configure structured logging with structlog."""

    # Clear any existing handlers
    logging.root.handlers.clear()

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )

    # Shared processors
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        add_app_context,
    ]

    if development and format_type == "console":
        # Human-readable console output for development
        shared_processors.extend(
            [
                structlog.processors.ExceptionPrettyPrinter(),
                structlog.dev.ConsoleRenderer(colors=True),
            ]
        )
    else:
        # JSON output for production
        shared_processors.extend(
            [structlog.processors.format_exc_info, structlog.processors.JSONRenderer()]
        )

    # Configure structlog
    structlog.configure(
        processors=shared_processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Silence noisy third-party loggers
    for logger_name in [
        "uvicorn.access",
        "sqlalchemy.engine",
        "asyncio",
        "multipart",
    ]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def get_logger(name: str = __name__) -> structlog.BoundLogger:
    """Get a configured logger instance."""
    return structlog.get_logger(name)


# Logging utilities for FastAPI middleware
def log_request_response(
    method: str,
    url: str,
    status_code: int,
    duration: float,
    extra: Dict[str, Any] | None = None,
) -> None:
    """Log HTTP request/response information."""
    logger = get_logger("http")
    logger.info(
        "HTTP request completed",
        method=method,
        url=str(url),
        status_code=status_code,
        duration_ms=round(duration * 1000, 2),
        **(extra or {}),
    )
