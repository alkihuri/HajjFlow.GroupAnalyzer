"""User authorization: whitelist of Telegram user IDs."""

ALLOWED_USER_IDS: list[int] = [
    123456789,
    987654321,
]


def is_user_allowed(user_id: int) -> bool:
    """Return True if the Telegram user ID is whitelisted."""
    return user_id in ALLOWED_USER_IDS
