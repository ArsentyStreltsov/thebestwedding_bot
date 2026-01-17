import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import Config
from database import Database, init_db
from handlers import start_router, wishlist_router, info_router, contact_router

# Импорт scheduler для запланированных пушей
try:
    from admin.scheduler import send_scheduled_pushes
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False

# Настройка логирования
logging.basicConfig(
    level=logging.INFO if not Config.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска бота"""
    try:
        # Валидация конфигурации
        Config.validate()
        logger.info("Конфигурация загружена успешно")
        
        # Инициализация базы данных
        await Database.create_pool()
        logger.info("Подключение к базе данных установлено")
        
        # Создание таблиц
        await init_db()
        logger.info("Таблицы базы данных проверены/созданы")
        
        # Инициализация бота и диспетчера
        bot = Bot(token=Config.BOT_TOKEN)
        dp = Dispatcher(storage=MemoryStorage())
        
        # Регистрация роутеров
        dp.include_router(start_router)
        dp.include_router(wishlist_router)
        dp.include_router(info_router)
        dp.include_router(contact_router)
        
        logger.info("Бот запущен и готов к работе")
        
        # Запуск фоновой задачи для отправки запланированных пушей
        if SCHEDULER_AVAILABLE:
            asyncio.create_task(send_scheduled_pushes())
            logger.info("Scheduler для пушей запущен")
        
        # Запуск polling
        await dp.start_polling(bot, skip_updates=True)
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}", exc_info=True)
    finally:
        # Закрытие подключений
        await Database.close_pool()
        logger.info("Подключения закрыты")


if __name__ == "__main__":
    asyncio.run(main())
