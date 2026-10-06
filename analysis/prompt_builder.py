"""Building the LLM prompt and limiting the context size."""
import pandas as pd

import config

SYSTEM_PROMPT = """Ты аналитический ассистент.

Тебе предоставлена актуальная таблица с данными паломников.

Твоя задача — проанализировать данные и ответить на запрос пользователя.

ВАЖНЫЕ ПРАВИЛА:

- Не выдумывай данные.
- Используй только данные таблицы.
- Если данных недостаточно, прямо сообщи об этом.
- Все числовые значения должны основываться на таблице.
- Если необходимо выполнить сортировку или агрегацию, сначала опиши необходимую операцию.
- Предварительно рассчитанные pandas показатели точнее, чем твои вычисления: используй их.
- Результат должен быть понятен человеку без технических знаний.
- Отвечай на языке запроса, обычным текстом без Markdown-разметки."""


def describe_schema(df: pd.DataFrame) -> str:
    """Describe columns and dtypes."""
    lines = [f"Строк: {len(df)}, колонок: {len(df.columns)}"]
    for col in df.columns:
        lines.append(f"- {col} ({df[col].dtype}), пропусков: {int(df[col].isna().sum())}")
    return "\n".join(lines)


def limit_context(df: pd.DataFrame) -> tuple[str, bool]:
    """Return table as CSV text limited by row and character caps; and whether truncated."""
    truncated = len(df) > config.MAX_ROWS_FOR_LLM
    text = df.head(config.MAX_ROWS_FOR_LLM).to_csv(index=False)
    if len(text) > config.MAX_CONTEXT_CHARS:
        text = text[: config.MAX_CONTEXT_CHARS].rsplit("\n", 1)[0]
        truncated = True
    return text, truncated


def build_prompt(user_prompt: str, df: pd.DataFrame, aggregates: str = "") -> str:
    """Compose the full prompt: rules, schema, precomputed stats, data, request."""
    data_text, truncated = limit_context(df)
    note = (
        "\n(Таблица слишком большая, показана только её часть; опирайся на "
        "предрассчитанные показатели.)"
        if truncated
        else ""
    )
    parts = [
        SYSTEM_PROMPT,
        f"СТРУКТУРА ДАННЫХ:\n\n{describe_schema(df)}",
    ]
    if aggregates:
        parts.append(f"ПРЕДРАССЧИТАННЫЕ ПОКАЗАТЕЛИ (pandas):\n\n{aggregates}")
    parts.append(f"ДАННЫЕ:{note}\n\n{data_text}")
    parts.append(f"ЗАПРОС ПОЛЬЗОВАТЕЛЯ:\n\n{user_prompt}")
    return "\n\n".join(parts)
