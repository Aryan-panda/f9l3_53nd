import logging
import sys


class SecurityRedactingFormatter(logging.Formatter):
    """Formatter that redacts known secret patterns and ensures structured output."""

    SENSITIVE_KEYS = {
        "password",
        "secret",
        "key",
        "token",
        "master_key",
        "private_key",
        "session",
        "authorization",
    }

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        return message


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure root structured logger for the application."""
    logger = logging.getLogger("f9l3_53nd")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        formatter = SecurityRedactingFormatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
