import logging
import sys
from typing import Any

import structlog


def setup_logging(log_level: str = "INFO") -> None:
    """Configures structured logging (JSON for Prod, Console for Dev)."""

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Decide renderer based on environment (interactive vs container)
    if sys.stderr.isatty():
        # Pretty colors for local dev
        processors = shared_processors + [structlog.dev.ConsoleRenderer()]
    else:
        # JSON for Docker/Production (Parsable by Datadog/Loki)
        processors = shared_processors + [structlog.processors.JSONRenderer()]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Redirect standard library logging to structlog
    logging.basicConfig(format="%(message)s", level=log_level, stream=sys.stdout)
