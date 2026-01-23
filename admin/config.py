import os
from dotenv import load_dotenv

load_dotenv()


class AdminConfig:
    """Конфигурация админ-панели"""
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # Admin Panel
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    
    # Telegram Bot (для отправки пушей)
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    @classmethod
    def validate(cls) -> bool:
        """Проверка наличия обязательных переменных окружения"""
        if not cls.DATABASE_URL:
            raise ValueError("DATABASE_URL не установлен в .env файле")
        if not cls.ADMIN_PASSWORD:
            raise ValueError("ADMIN_PASSWORD не установлен в .env файле")
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не установлен в .env файле")
        if not cls.SECRET_KEY:
            raise ValueError("SECRET_KEY не установлен в .env файле")
        return True
