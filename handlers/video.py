import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, URLInputFile
from keyboards.main_menu import get_main_menu_keyboard
from messages import get_video_text
from config import Config

logger = logging.getLogger(__name__)
router = Router()


def get_telegram_file_url(file_path: str) -> str:
    """
    Формирует постоянный URL к файлу в Telegram через Bot API.
    Этот URL работает постоянно и не устаревает.
    """
    return f"https://api.telegram.org/file/bot{Config.BOT_TOKEN}/{file_path}"


@router.message(F.text == "🎥 Видео-приглашение")
async def video_handler(message: Message, bot: Bot):
    """Обработчик раздела видео-приглашения"""
    # Отправляем текст
    await message.answer(
        get_video_text(),
        reply_markup=get_main_menu_keyboard()
    )
    
    # Приоритет отправки (от самого надежного к менее надежному):
    # 1. VIDEO_FILE_PATH (постоянный путь через Telegram Bot API) - самый надежный
    # 2. VIDEO_URL (внешний URL)
    # 3. VIDEO_FILE_ID (временный file_id)
    video_sent = False
    
    # Вариант 1: Отправка по file_path через Telegram Bot API (постоянный, самый надежный)
    if Config.VIDEO_FILE_PATH:
        try:
            logger.info(f"Отправка видео по file_path: {Config.VIDEO_FILE_PATH[:30]}...")
            telegram_url = get_telegram_file_url(Config.VIDEO_FILE_PATH)
            video_file = URLInputFile(telegram_url)
            await message.answer_video(
                video_file,
                reply_markup=get_main_menu_keyboard()
            )
            logger.info("Видео успешно отправлено по file_path (Telegram Bot API)")
            video_sent = True
        except Exception as e:
            logger.error(f"Ошибка отправки видео по file_path: {e}")
    
    # Вариант 2: Отправка по внешнему URL
    if not video_sent and Config.VIDEO_URL:
        try:
            logger.info(f"Отправка видео по URL: {Config.VIDEO_URL[:50]}...")
            video_file = URLInputFile(Config.VIDEO_URL)
            await message.answer_video(
                video_file,
                reply_markup=get_main_menu_keyboard()
            )
            logger.info("Видео успешно отправлено по URL")
            video_sent = True
        except Exception as e:
            logger.error(f"Ошибка отправки видео по URL: {e}")
    
    # Вариант 3: Отправка по file_id (временный, может устареть)
    if not video_sent and Config.VIDEO_FILE_ID:
        try:
            logger.info(f"Отправка видео с file_id: {Config.VIDEO_FILE_ID[:20]}...")
            await message.answer_video(
                Config.VIDEO_FILE_ID,
                reply_markup=get_main_menu_keyboard()
            )
            logger.info("Видео успешно отправлено по file_id")
            video_sent = True
        except Exception as e:
            logger.error(f"Ошибка отправки видео по file_id: {e}")
            # Если file_id устарел, предлагаем обновить
            if "wrong file identifier" in str(e).lower():
                logger.warning("file_id устарел, рекомендуется получить file_path")
    
    # Если ничего не сработало
    if not video_sent:
        logger.warning("Не удалось отправить видео: ни один способ не работает")
        try:
            await message.answer(
                "❌ Не удалось отправить видео. Проверьте настройки бота.",
                reply_markup=get_main_menu_keyboard()
            )
        except:
            pass


@router.message(F.video)
async def video_file_id_handler(message: Message, bot: Bot):
    """Обработчик для получения file_id и file_path видео (для админов)"""
    # Проверяем, что отправитель - админ
    if message.from_user.id in Config.ADMIN_USER_IDS:
        video = message.video
        file_id = video.file_id
        
        # Получаем file_path через Bot API (постоянный путь)
        # ВАЖНО: работает только для файлов до 20 МБ!
        file_path = None
        file_too_big = False
        try:
            file_info = await bot.get_file(file_id)
            file_path = file_info.file_path
        except Exception as e:
            error_msg = str(e).lower()
            if "too big" in error_msg or "file is too big" in error_msg:
                file_too_big = True
                logger.warning(f"Видео слишком большое (>20 МБ), getFile недоступен")
            else:
                logger.error(f"Ошибка получения file_path: {e}")
        
        # Получаем размер файла для информации
        file_size_mb = None
        if video.file_size:
            file_size_mb = round(video.file_size / (1024 * 1024), 2)
        
        # Формируем ответ с информацией
        response_text = f"📹 Информация о видео:\n\n"
        response_text += f"<b>file_id:</b>\n<code>{file_id}</code>\n\n"
        
        if file_size_mb:
            response_text += f"<b>Размер:</b> {file_size_mb} МБ\n\n"
        
        if file_path:
            telegram_url = get_telegram_file_url(file_path)
            response_text += f"<b>file_path (постоянный, рекомендуется):</b>\n<code>{file_path}</code>\n\n"
            response_text += f"<b>Постоянный URL:</b>\n<code>{telegram_url}</code>\n\n"
            response_text += f"💡 <b>Добавьте в Railway Variables:</b>\n"
            response_text += f"<code>VIDEO_FILE_PATH={file_path}</code>\n\n"
            response_text += f"Этот путь <b>не устаревает</b> и работает постоянно! ✅"
        elif file_too_big:
            response_text += f"⚠️ <b>Видео слишком большое (>20 МБ)</b>\n\n"
            response_text += f"Для больших видео нужно использовать <b>внешний URL</b>:\n\n"
            response_text += f"1️⃣ Загрузите видео в облачное хранилище:\n"
            response_text += f"   • Google Drive (публичная ссылка)\n"
            response_text += f"   • Яндекс.Диск (публичная ссылка)\n"
            response_text += f"   • Cloudflare R2 / AWS S3\n"
            response_text += f"   • Или другой хостинг\n\n"
            response_text += f"2️⃣ Получите прямую ссылку на файл (URL должен вести напрямую к .mp4)\n\n"
            response_text += f"3️⃣ Добавьте в Railway Variables:\n"
            response_text += f"<code>VIDEO_URL=https://ваш-хостинг.com/video.mp4</code>\n\n"
            response_text += f"💡 <b>Временное решение:</b> Используйте file_id:\n"
            response_text += f"<code>VIDEO_FILE_ID={file_id}</code>\n"
            response_text += f"⚠️ Но он может устареть через несколько недель."
        else:
            response_text += f"⚠️ Не удалось получить file_path. Используйте:\n"
            response_text += f"<code>VIDEO_FILE_ID={file_id}</code>\n\n"
            response_text += f"⚠️ <b>Внимание:</b> file_id может устареть через несколько недель.\n\n"
            response_text += f"💡 Для надежности лучше использовать <b>VIDEO_URL</b> с внешним хостингом."
        
        await message.answer(
            response_text,
            parse_mode="HTML"
        )
