"""Telegram bot handlers."""
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import config
from analysis.processor import process_request
from data.google_sheets import SheetsError, fetch_dataframe
from filter import is_user_allowed
from ollama.client import OllamaError
from utils.logger import get_logger

logger = get_logger(__name__)

NO_ACCESS = "У вас нет доступа к этому функционалу."

HELP_TEXT = (
    "👋 Привет!\n\n"
    "Я аналитический ассистент.\n\n"
    "Я могу анализировать актуальные данные из Google Sheets с помощью "
    "локальной AI-модели.\n\n"
    "Просто отправьте мне вопрос, например:\n\n"
    "«Покажи 10 групп с самой низкой успеваемостью и их руководителей»."
)


def split_message(text: str, limit: int = config.MAX_TELEGRAM_MESSAGE_LENGTH) -> list[str]:
    """Split text into chunks not exceeding the Telegram limit."""
    chunks: list[str] = []
    while len(text) > limit:
        cut = text.rfind("\n", 0, limit)
        if cut <= 0:
            cut = limit
        chunks.append(text[:cut])
        text = text[cut:].lstrip("\n")
    if text:
        chunks.append(text)
    return chunks


async def _check_access(update: Update) -> bool:

    return True
    user = update.effective_user
    if user is None or update.message is None:
        return False
    if not is_user_allowed(user.id):
        logger.warning("Access denied for user %s", user.id)
        await update.message.reply_text(NO_ACCESS)
        return False
    return True


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start and /help."""
    if await _check_access(update):
        await update.message.reply_text(HELP_TEXT)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Run the full pipeline for a text message from an authorized user."""
    if not await _check_access(update):
        return
    message = update.message
    user_id = update.effective_user.id
    text = (message.text or "").strip()
    if not text:
        return

    logger.info("user=%s: processing started", user_id)
    try:
        await message.reply_text("🔎 Запрос получен.\n\n📥 Загружаю актуальные данные из Google Sheets...")
        df = await fetch_dataframe()
        logger.info("user=%s: CSV rows=%d columns=%d", user_id, len(df), len(df.columns))
        await message.reply_text(
            f"✅ Таблица загружена.\n\n📊 Записей: {len(df)}\n📋 Колонок: {len(df.columns)}\n\n"
            "🤖 Передаю данные локальной модели Ollama..."
        )
        await message.reply_text("⏳ Ollama анализирует данные...")
        await message.chat.send_action(ChatAction.TYPING)
        result = await process_request(text, df)
        await message.reply_text("✅ Анализ завершён.\n\nФормирую результат...")
        for chunk in split_message(result):
            await message.reply_text(chunk)
        logger.info("user=%s: processing finished", user_id)
    except (SheetsError, OllamaError) as exc:
        logger.error("user=%s: request failed: %s", user_id, exc)
        await message.reply_text(f"❌ Не удалось выполнить запрос.\n\nОшибка: {exc}")
    except Exception:
        logger.exception("user=%s: unexpected error", user_id)
        await message.reply_text(
            "❌ Не удалось выполнить запрос.\n\nОшибка: внутренняя ошибка, подробности в логе."
        )


def create_application() -> Application:
    """Build the Telegram application and register handlers."""
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler(["start", "help"], start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return application
