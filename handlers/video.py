import logging
from aiogram import Router, F
from aiogram.types import Message
from keyboards.main_menu import get_main_menu_keyboard
from messages import get_video_text
from config import Config

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == "🎥 Видео-приглашение")
async def video_handler(message: Message):
    """Обработчик раздела видео-приглашения"""
    # Отправляем текст
    await message.answer(
        get_video_text(),
        reply_markup=get_main_menu_keyboard()
    )
    
    # Если есть file_id видео, отправляем его
    if Config.VIDEO_FILE_ID:
        try:
            logger.info(f"Отправка видео с file_id: {Config.VIDEO_FILE_ID[:20]}...")
            await message.answer_video(
                Config.VIDEO_FILE_ID,
                reply_markup=get_main_menu_keyboard()
            )
            logger.info("Видео успешно отправлено")
        except Exception as e:
            logger.error(f"Ошибка отправки видео: {e}")
            # Пытаемся отправить пользователю сообщение об ошибке
            try:
                await message.answer(
                    "❌ Не удалось отправить видео. Проверьте настройки бота.",
                    reply_markup=get_main_menu_keyboard()
                )
            except:
                pass
    else:
        logger.warning("VIDEO_FILE_ID не установлен в переменных окружения")


@router.message(F.video)
async def video_file_id_handler(message: Message):
    """Обработчик для получения file_id видео (для админов)"""
    # Проверяем, что отправитель - админ
    if message.from_user.id in Config.ADMIN_USER_IDS:
        video = message.video
        file_id = video.file_id
        
        # Используем HTML для безопасного форматирования
        await message.answer(
            f"📹 file_id видео:\n\n"
            f"<code>{file_id}</code>\n\n"
            f"💡 Добавьте в .env или .env.local:\n"
            f"<code>VIDEO_FILE_ID={file_id}</code>",
            parse_mode="HTML"
        )
