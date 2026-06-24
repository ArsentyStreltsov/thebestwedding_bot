import os
from dotenv import load_dotenv

# Загружаем .env.local для локальной разработки, если он существует
# Иначе загружаем обычный .env (для продакшн)
if os.path.exists(".env.local"):
    load_dotenv(".env.local")
else:
    load_dotenv()


class Config:
    """Конфигурация приложения"""

    # Telegram Bot
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # Admin
    ADMIN_USER_IDS: list[int] = [
        int(uid.strip())
        for uid in os.getenv("ADMIN_USER_IDS", "").split(",")
        if uid.strip().isdigit()
    ]

    # Settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Logs Group (для отправки важных логов и ошибок)
    LOGS_GROUP_ID: str = os.getenv("LOGS_GROUP_ID", "")

    # Video
    VIDEO_FILE_ID: str = os.getenv("VIDEO_FILE_ID", "")

    # Webhook (WEBHOOK_URL — предпочтительно на сервере; WEBHOOK_HOST — для локальной разработки)
    WEBHOOK_HOST: str = os.getenv("WEBHOOK_URL", os.getenv("WEBHOOK_HOST", ""))
    _webhook_path = os.getenv("WEBHOOK_PATH", "/webhook")
    WEBHOOK_PATH: str = (
        _webhook_path if _webhook_path.startswith("/") or _webhook_path == "" else f"/{_webhook_path}"
    )
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "")

    # Сеть: на Hetzner HOST=127.0.0.1, снаружи — через Nginx
    HOST: str = os.getenv("HOST", "127.0.0.1")
    WEBHOOK_PORT: int = int(os.getenv("PORT", os.getenv("WEBHOOK_PORT", "8002")))

    @classmethod
    def validate(cls) -> bool:
        """Проверка наличия обязательных переменных окружения"""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не установлен в .env файле")
        if not cls.DATABASE_URL:
            raise ValueError("DATABASE_URL не установлен в .env файле")
        if not cls.WEBHOOK_HOST:
            raise ValueError("WEBHOOK_URL (или WEBHOOK_HOST) не установлен в .env файле")
        if not cls.WEBHOOK_SECRET:
            raise ValueError("WEBHOOK_SECRET не установлен в .env файле")
        return True
