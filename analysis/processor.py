"""Analysis pipeline: pandas precomputation + LLM interpretation."""
import pandas as pd

from analysis.prompt_builder import build_prompt
from ollama import client as ollama_client
from utils.logger import get_logger

logger = get_logger(__name__)

GROUP_HINTS = ("групп", "group")
MAX_GROUPS_IN_SUMMARY = 200


def compute_aggregates(df: pd.DataFrame) -> str:
    """Compute numeric statistics and per-group means with pandas."""
    numeric = df.select_dtypes("number")
    parts: list[str] = []
    if not numeric.empty:
        stats = numeric.describe().T[["count", "mean", "min", "max"]].round(2)
        parts.append("Статистика числовых колонок:\n" + stats.to_string())

    group_cols = [c for c in df.columns if any(h in c.lower() for h in GROUP_HINTS)]
    if group_cols and not numeric.empty:
        gcol = group_cols[0]
        numeric_cols = [c for c in numeric.columns if c != gcol]
        if numeric_cols:
            grouped = df.groupby(gcol)[numeric_cols].mean().round(2)
            counts = df.groupby(gcol).size().rename("записей")
            summary = grouped.join(counts).head(MAX_GROUPS_IN_SUMMARY)
            parts.append(
                f"Количество уникальных значений «{gcol}»: {df[gcol].nunique()}\n"
                f"Средние значения по «{gcol}»:\n" + summary.to_csv()
            )
    return "\n\n".join(parts)


async def process_request(user_prompt: str, df: pd.DataFrame) -> str:
    """Run the analysis for one request and return the LLM answer."""
    aggregates = compute_aggregates(df)
    prompt = build_prompt(user_prompt, df, aggregates)
    await savepromttofile(prompt, "latest_prompt.txt")
    logger.info("Sending request to Ollama (prompt %d chars)", len(prompt))

    return await ollama_client.generate(prompt)


async def savepromttofile(prompt: str, filename: str) -> None:
    """Save the given prompt to a file asynchronously."""
    import aiofiles

    async with aiofiles.open(filename, "w") as f:
        await f.write(prompt)