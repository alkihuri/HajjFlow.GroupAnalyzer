"""Entry point: python main.py"""
import config
from bot.telegram_bot import create_application
from utils.logger import setup_logging


def main() -> None:
    """Validate config, create the bot and start polling."""
    setup_logging()
    config.validate()
    create_application().run_polling()


if __name__ == "__main__":
    main()
