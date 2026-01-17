import os
from dotenv import load_dotenv

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
    
    @classmethod
    def validate(cls) -> bool:
        """Проверка наличия обязательных переменных окружения"""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не установлен в .env файле")
        if not cls.DATABASE_URL:
            raise ValueError("DATABASE_URL не установлен в .env файле")
        return True
