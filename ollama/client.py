"""Async client for the local Ollama API."""
import asyncio
import time

import httpx

import config
from utils.logger import get_logger

logger = get_logger(__name__)

_semaphore: asyncio.Semaphore | None = None


class OllamaError(Exception):
    """Raised for Ollama failures, with a user-friendly message."""


def _get_semaphore() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(max(1, config.OLLAMA_CONCURRENCY))
    return _semaphore


async def generate(prompt: str) -> str:
    """Send a prompt to Ollama and return the response text.

    Requests are queued by a semaphore so a local model is not overloaded.
    """
    payload = {"model": config.OLLAMA_MODEL, "prompt": prompt, "stream": False}
    url = f"{config.OLLAMA_URL.rstrip('/')}/api/generate"
    async with _get_semaphore():
        started = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=config.OLLAMA_TIMEOUT) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.ConnectError as exc:
            logger.error("Ollama unavailable at %s", config.OLLAMA_URL)
            raise OllamaError(
                "Ollama недоступна. Убедитесь, что она запущена локально."
            ) from exc
        except httpx.TimeoutException as exc:
            logger.error("Ollama timeout after %ss", config.OLLAMA_TIMEOUT)
            raise OllamaError("Ollama не ответила вовремя.") from exc
        except httpx.HTTPStatusError as exc:
            logger.error("Ollama error %s: %s", exc.response.status_code, exc.response.text[:500])
            raise OllamaError(
                f"Ошибка модели Ollama (HTTP {exc.response.status_code}). "
                f"Проверьте, что модель «{config.OLLAMA_MODEL}» скачана."
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            logger.error("Ollama request failed: %s", exc)
            raise OllamaError("Не удалось получить ответ от Ollama.") from exc
        logger.info("Ollama responded in %.1fs", time.monotonic() - started)

    text = (data.get("response") or "").strip()
    if not text:
        raise OllamaError("Модель вернула пустой ответ.")
    return text
