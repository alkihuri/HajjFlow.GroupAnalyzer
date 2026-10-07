"""Logging setup."""
import logging


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logging; also silence HTTP libs that log URLs with secrets."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    # httpx/telegram log full request URLs, which contain the bot token.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger."""
    return logging.getLogger(name)
