import asyncio
import json
import logging
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from config import Config
from database import Database, init_db
from handlers import start_router, wishlist_router, info_router, dresscode_router, disclaimer_router, video_router
from utils.telegram_logger import TelegramGroupHandler, init_telegram_logger, close_telegram_logger

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)

logging.getLogger("aiogram").setLevel(logging.CRITICAL)
logging.getLogger("asyncpg").setLevel(logging.CRITICAL)
logging.getLogger("aiohttp").setLevel(logging.CRITICAL)
logging.getLogger("aiohttp.access").setLevel(logging.CRITICAL)
logging.getLogger("uvicorn").setLevel(logging.CRITICAL)
logging.getLogger("uvicorn.access").setLevel(logging.CRITICAL)
logging.getLogger("fastapi").setLevel(logging.CRITICAL)

if Config.LOGS_GROUP_ID:
    telegram_handler = TelegramGroupHandler()
    telegram_handler.setLevel(logging.ERROR)
    logging.getLogger().addHandler(telegram_handler)


async def register_webhook_loop(bot: Bot) -> None:
    """Повторяет setWebhook, пока Telegram не примет URL (например, пока не поднимется DNS)."""
    host = Config.WEBHOOK_HOST.rstrip("/")
    webhook_url = f"{host}{Config.WEBHOOK_PATH}"
    while True:
        try:
            await bot.set_webhook(
                webhook_url,
                secret_token=Config.WEBHOOK_SECRET,
            )
            logger.info("Webhook установлен: %s", webhook_url)
            return
        except Exception as e:
            logger.error("Webhook не установлен, повтор через 60с: %s", e)
            await asyncio.sleep(60)


async def on_startup(bot: Bot) -> None:
    await init_telegram_logger()
    asyncio.create_task(register_webhook_loop(bot))


async def on_shutdown(bot: Bot) -> None:
    await bot.session.close()
    await close_telegram_logger()


async def init_bot():
    Config.validate()

    await Database.create_pool()
    await init_db()

    bot = Bot(token=Config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start_router)
    dp.include_router(wishlist_router)
    dp.include_router(info_router)
    dp.include_router(dresscode_router)
    dp.include_router(disclaimer_router)
    dp.include_router(video_router)

    return bot, dp


async def main():
    try:
        bot, dp = await init_bot()

        app = web.Application()

        @web.middleware
        async def error_logging_middleware(request, handler):
            try:
                return await handler(request)
            except Exception as e:
                logger.error("Необработанное исключение в webhook: %s", e, exc_info=True)
                raise

        app.middlewares.append(error_logging_middleware)

        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
            secret_token=Config.WEBHOOK_SECRET,
        )
        webhook_requests_handler.register(app, path=Config.WEBHOOK_PATH)

        async def health_check(request):
            return web.Response(
                text=json.dumps({"ok": True}),
                content_type="application/json",
            )

        app.router.add_get("/health", health_check)

        setup_application(app, dp, bot=bot)

        async def startup_handler(app):
            await on_startup(bot)

        async def shutdown_handler(app):
            await on_shutdown(bot)

        app.on_startup.append(startup_handler)
        app.on_shutdown.append(shutdown_handler)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, Config.HOST, Config.WEBHOOK_PORT)
        await site.start()

        logger.info("Бот запущен на %s:%s", Config.HOST, Config.WEBHOOK_PORT)

        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            pass
        finally:
            await runner.cleanup()

    except KeyboardInterrupt:
        pass
    except Exception as e:
        error_msg = str(e)
        if "nodename nor servname" in error_msg or "Connection" in error_msg:
            logger.error("Ошибка подключения к базе данных: %s", error_msg)
            logger.error("Проверьте настройки DATABASE_URL в файле .env")
        elif "WEBHOOK" in error_msg:
            logger.error("%s", error_msg)
        else:
            logger.error("Ошибка при запуске бота: %s", error_msg)
        sys.exit(1)
    finally:
        try:
            await Database.close_pool()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
