# Telegram + Ollama Analytics

Локальный Telegram-бот: по запросу авторизованного пользователя скачивает актуальный CSV из публичной Google Sheets таблицы, считает показатели через pandas и передаёт данные локальной LLM (Ollama) для интерпретации. Результат отправляется в Telegram.

```
Telegram → проверка User ID → CSV из Google Sheets → pandas → prompt → Ollama → Telegram
```

## Установка

```bash
git clone https://github.com/alkihuri/HajjFlow.GroupAnalyzer.git
cd HajjFlow.GroupAnalyzer

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Установка Ollama

Установите Ollama с https://ollama.com и запустите её локально.

```bash
ollama list
ollama pull phi3
ollama run phi3
```

## Настройка Telegram

Получите токен у [@BotFather](https://t.me/BotFather) (`/newbot`), затем `cp .env.example .env` и заполните `TELEGRAM_BOT_TOKEN`.

## Настройка Google Sheets

Файл → Поделиться → Опубликовать в интернете → выберите лист и формат **CSV**. Скопируйте ссылку вида
`https://docs.google.com/spreadsheets/d/.../pub?output=csv` в `GOOGLE_SHEETS_CSV_URL`.

Дополнительные переменные `.env` (необязательно): `OLLAMA_TIMEOUT`, `MAX_ROWS_FOR_LLM`, `MAX_CONTEXT_CHARS`, `OLLAMA_CONCURRENCY`.

## Добавление пользователей

В `filter.py`:

```python
ALLOWED_USER_IDS = [
    123456789,
]
```

Проверяется только Telegram `user_id` (не username), до загрузки таблицы.

## Запуск

```bash
python main.py
```

## Архитектура

- `bot/` — Telegram handlers; `data/` — загрузка таблиц; `analysis/` — pandas-агрегаты и prompt; `ollama/` — клиент (с очередью запросов); `filter.py` — whitelist.
- Для новых источников данных/аналитики добавляйте модули в `data/` и `analysis/`, бот менять не нужно.
- Большие таблицы ограничиваются `MAX_ROWS_FOR_LLM`; LLM получает pandas-агрегаты.
