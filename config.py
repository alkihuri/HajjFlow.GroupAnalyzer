"""Application configuration loaded from environment / .env file."""
import os

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "phi3")
GOOGLE_SHEETS_CSV_URL: str = os.getenv("GOOGLE_SHEETS_CSV_URL", "")

OLLAMA_TIMEOUT: int = int(os.getenv("OLLAMA_TIMEOUT", "300"))
MAX_TELEGRAM_MESSAGE_LENGTH: int = 4096
MAX_ROWS_FOR_LLM: int = int(os.getenv("MAX_ROWS_FOR_LLM", "5000"))
# Hard cap on characters of raw table data placed in the prompt.
MAX_CONTEXT_CHARS: int = int(os.getenv("MAX_CONTEXT_CHARS", "60000"))
# Number of simultaneous Ollama requests (others wait in a queue).
OLLAMA_CONCURRENCY: int = int(os.getenv("OLLAMA_CONCURRENCY", "1"))
SHEETS_TIMEOUT: int = int(os.getenv("SHEETS_TIMEOUT", "60"))


def validate() -> None:
    """Raise RuntimeError if required settings are missing."""
    missing = [
        name
        for name, value in (
            ("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN),
            ("GOOGLE_SHEETS_CSV_URL", GOOGLE_SHEETS_CSV_URL),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing required settings in .env: {', '.join(missing)}")
