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
    
    # Video
    VIDEO_FILE_ID: str = os.getenv("VIDEO_FILE_ID", "")  # file_id видео из Telegram
    
    # Calendar Server URL for .ics file
    CALENDAR_SERVER_URL: str = os.getenv("CALENDAR_SERVER_URL", "")  # URL календарного сервера на Railway
    
    # Webhook
    WEBHOOK_HOST: str = os.getenv("WEBHOOK_HOST", "")  # URL для webhook (например: https://your-app.railway.app)
    # Путь для webhook (должен начинаться с / или быть пустым)
    _webhook_path = os.getenv("WEBHOOK_PATH", "/webhook")
    WEBHOOK_PATH: str = _webhook_path if _webhook_path.startswith("/") or _webhook_path == "" else f"/{_webhook_path}"
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "")  # Секретный ключ для webhook (опционально)
    # Порт для веб-сервера (Railway использует переменную PORT, локально - 8001)
    WEBHOOK_PORT: int = int(os.getenv("PORT", os.getenv("WEBHOOK_PORT", "8001")))
    
    @classmethod
    def validate(cls) -> bool:
        """Проверка наличия обязательных переменных окружения"""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не установлен в .env файле")
        if not cls.DATABASE_URL:
            raise ValueError("DATABASE_URL не установлен в .env файле")
        # WEBHOOK_HOST обязателен только если не используется polling
        return True
