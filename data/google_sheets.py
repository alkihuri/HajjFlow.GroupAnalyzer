"""Loading of Google Sheets published as CSV."""
import io

import httpx
import pandas as pd

import config
from utils.logger import get_logger

logger = get_logger(__name__)


class SheetsError(Exception):
    """Raised when the table cannot be loaded."""


async def fetch_dataframe(url: str | None = None) -> pd.DataFrame:
    """Download the CSV on every call (fresh data) and parse it with pandas."""
    url = url or config.GOOGLE_SHEETS_CSV_URL
    try:
        async with httpx.AsyncClient(
            timeout=config.SHEETS_TIMEOUT, follow_redirects=True
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        logger.error("Google Sheets HTTP status %s", exc.response.status_code)
        raise SheetsError(
            f"Google Sheets вернул HTTP {exc.response.status_code}"
        ) from exc
    except httpx.HTTPError as exc:
        logger.error("Google Sheets request failed: %s", type(exc).__name__)
        raise SheetsError("Не удалось скачать таблицу Google Sheets") from exc

    try:
        df = pd.read_csv(io.StringIO(response.content.decode("utf-8-sig")))
    except Exception as exc:
        logger.error("CSV parse failed: %s", exc)
        raise SheetsError("Не удалось прочитать CSV таблицу") from exc

    df.columns = [str(c).strip() for c in df.columns]
    logger.info("CSV loaded: %d rows, %d columns", len(df), len(df.columns))
    return df
