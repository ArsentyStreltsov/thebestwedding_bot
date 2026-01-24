import asyncio
import logging
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from config import Config
from database import Database, init_db
from handlers import start_router, wishlist_router, info_router, dresscode_router, disclaimer_router, video_router

# Импорт scheduler для запланированных пушей
try:
    from admin.scheduler import send_scheduled_pushes
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False

# Настройка логирования
logging.basicConfig(
    level=logging.ERROR if not Config.DEBUG else logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# Уменьшаем уровень логирования для библиотек
logging.getLogger("aiogram").setLevel(logging.ERROR)
logging.getLogger("asyncpg").setLevel(logging.ERROR)
logging.getLogger("aiohttp").setLevel(logging.ERROR)
logging.getLogger("aiohttp.access").setLevel(logging.ERROR)


async def on_startup(bot: Bot) -> None:
    """Выполняется при запуске бота"""
    # Убираем слеш в конце WEBHOOK_HOST, если он есть
    host = Config.WEBHOOK_HOST.rstrip('/')
    # Формируем правильный URL
    webhook_url = f"{host}{Config.WEBHOOK_PATH}"
    await bot.set_webhook(
        webhook_url,
        secret_token=Config.WEBHOOK_SECRET if Config.WEBHOOK_SECRET else None
    )


async def on_shutdown(bot: Bot) -> None:
    """Выполняется при остановке бота"""
    await bot.session.close()


async def init_bot():
    """Инициализация бота и диспетчера"""
    # Валидация конфигурации
    Config.validate()
    
    # Проверка наличия WEBHOOK_HOST
    if not Config.WEBHOOK_HOST:
        raise ValueError("WEBHOOK_HOST не установлен в .env файле. Укажите URL для webhook (например: https://your-app.railway.app или https://your-ngrok-url.ngrok.io)")
    
    # Инициализация базы данных
    await Database.create_pool()
    
    # Создание таблиц
    await init_db()
    
    # Инициализация бота и диспетчера
    bot = Bot(token=Config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Регистрация роутеров
    dp.include_router(start_router)
    dp.include_router(wishlist_router)
    dp.include_router(info_router)
    dp.include_router(dresscode_router)
    dp.include_router(disclaimer_router)
    dp.include_router(video_router)
    
    # Запуск фоновой задачи для отправки запланированных пушей
    if SCHEDULER_AVAILABLE:
        try:
            from admin.database import AdminDatabase
            from admin.config import AdminConfig
            # Инициализируем AdminDatabase для scheduler
            AdminConfig.validate()
            await AdminDatabase.create_pool()
            asyncio.create_task(send_scheduled_pushes())
        except Exception as e:
            logger.warning(f"Scheduler не запущен: {e}")
    
    return bot, dp


async def main():
    """Главная функция запуска бота через webhook"""
    try:
        bot, dp = await init_bot()
        
        # Создаём веб-приложение
        app = web.Application()
        
        # Настраиваем webhook
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
            secret_token=Config.WEBHOOK_SECRET if Config.WEBHOOK_SECRET else None
        )
        webhook_requests_handler.register(app, path=Config.WEBHOOK_PATH)
        
        # Health check endpoint
        async def health_check(request):
            return web.Response(text="OK")
        
        app.router.add_get("/health", health_check)
        
        # Настройка startup и shutdown
        setup_application(app, dp, bot=bot)
        
        # Добавляем обработчики startup и shutdown
        async def startup_handler(app):
            await on_startup(bot)
        
        async def shutdown_handler(app):
            await on_shutdown(bot)
        
        app.on_startup.append(startup_handler)
        app.on_shutdown.append(shutdown_handler)
        
        # Запуск веб-сервера внутри существующего event loop
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", Config.WEBHOOK_PORT)
        await site.start()
        
        # Логируем только запуск бота
        logger.info("🤖 Бот запущен и готов к работе")
        
        # Ожидаем бесконечно (сервер работает)
        try:
            await asyncio.Future()  # Бесконечное ожидание
        except asyncio.CancelledError:
            pass
        finally:
            await runner.cleanup()
        
    except KeyboardInterrupt:
        pass
    except Exception as e:
        error_msg = str(e)
        # Показываем только краткую информацию об ошибке
        if "nodename nor servname" in error_msg or "Connection" in error_msg:
            logger.error(f"❌ Ошибка подключения к базе данных: {error_msg}")
            logger.error("💡 Проверьте настройки DATABASE_URL в файле .env")
        elif "WEBHOOK_HOST" in error_msg:
            logger.error(f"❌ {error_msg}")
        else:
            logger.error(f"❌ Ошибка при запуске бота: {error_msg}")
        sys.exit(1)
    finally:
        # Закрытие подключений
        try:
            await Database.close_pool()
            # Закрываем также AdminDatabase если был инициализирован
            if SCHEDULER_AVAILABLE:
                try:
                    from admin.database import AdminDatabase
                    await AdminDatabase.close_pool()
                except:
                    pass
            pass
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main())
