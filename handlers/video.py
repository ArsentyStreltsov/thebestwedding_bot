import logging
from aiogram import Router, F, Bot
from aiogram.types import Message
from keyboards.main_menu import get_main_menu_keyboard
from messages import get_video_text
from config import Config

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == "🎥 Видео-приглашение")
async def video_handler(message: Message):
    """Обработчик раздела видео-приглашения"""
    
    # Проверяем наличие VIDEO_FILE_ID
    if not Config.VIDEO_FILE_ID:
        logger.warning("VIDEO_FILE_ID не установлен в конфигурации")
        await message.answer(
            "❌ Видео временно недоступно. Обратитесь к администратору.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Отправка видео по file_id
    try:
        logger.info(f"Попытка отправки видео по file_id: {Config.VIDEO_FILE_ID[:20]}...")
        await message.answer_video(
            Config.VIDEO_FILE_ID,
            caption=get_video_text(),  # Текст отправляется вместе с видео
            reply_markup=get_main_menu_keyboard()
        )
        logger.info("✅ Видео успешно отправлено по file_id")
        
    except Exception as e:
        error_msg = str(e).lower()
        logger.error(f"❌ Ошибка отправки видео по file_id: {e}")
        
        # Определяем тип ошибки для более точного сообщения
        if "wrong file identifier" in error_msg or "file not found" in error_msg:
            logger.warning("⚠️ file_id устарел или неверный")
            await message.answer(
                "❌ Не удалось отправить видео.\n\n"
                "⚠️ file_id устарел или неверный.\n\n"
                "💡 Решение: отправьте видео файлом боту заново и получите новый file_id.",
                reply_markup=get_main_menu_keyboard()
            )
        elif "bad request" in error_msg:
            logger.warning("⚠️ Неверный запрос к Telegram API")
            await message.answer(
                "❌ Не удалось отправить видео.\n\n"
                "⚠️ Проблема с запросом к Telegram API.\n\n"
                "Проверьте настройки бота или обратитесь к администратору.",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            logger.error(f"⚠️ Неизвестная ошибка при отправке видео: {e}")
            await message.answer(
                "❌ Не удалось отправить видео.\n\n"
                "Возможные причины:\n"
                "• file_id устарел\n"
                "• Проблемы с Telegram API\n"
                "• Неверные настройки бота\n\n"
                "Проверьте настройки бота или обратитесь к администратору.",
                reply_markup=get_main_menu_keyboard()
            )


@router.message(F.video)
async def video_file_id_handler(message: Message, bot: Bot):
    """Обработчик для получения file_id видео (для админов)"""
    # Проверяем, что отправитель - админ
    if message.from_user.id in Config.ADMIN_USER_IDS:
        video = message.video
        file_id = video.file_id
        
        logger.info(f"Админ {message.from_user.id} отправил видео, получен file_id: {file_id[:20]}...")
        
        # Получаем размер файла для информации
        file_size_mb = None
        if video.file_size:
            file_size_mb = round(video.file_size / (1024 * 1024), 2)
            logger.info(f"Размер видео: {file_size_mb} МБ")
        
        # Формируем ответ с информацией
        response_text = f"📹 <b>Информация о видео:</b>\n\n"
        response_text += f"<b>file_id:</b>\n<code>{file_id}</code>\n\n"
        
        if file_size_mb:
            response_text += f"<b>Размер:</b> {file_size_mb} МБ\n\n"
        
        response_text += f"✅ <b>Этот file_id можно использовать для файлов ЛЮБОГО размера!</b>\n\n"
        response_text += f"💡 <b>Добавьте в Railway Variables:</b>\n"
        response_text += f"<code>VIDEO_FILE_ID={file_id}</code>\n\n"
        response_text += f"📌 <b>Как это работает:</b>\n"
        response_text += f"• Telegram уже хранит это видео на своих серверах\n"
        response_text += f"• file_id позволяет отправить его без повторной загрузки\n"
        response_text += f"• Нет лимита на размер файла при использовании file_id\n"
        response_text += f"• Отправка происходит мгновенно (из кеша Telegram)\n\n"
        response_text += f"🎯 <b>Важно для стабильности:</b>\n"
        response_text += f"• <b>file_id из входящих сообщений</b> (когда ты отправляешь боту) - более стабильные\n"
        response_text += f"• <b>file_id из канала</b> - самые стабильные (работают годами)\n\n"
        response_text += f"💡 <b>Рекомендация:</b> Для максимальной стабильности загрузи видео в канал, добавь бота как админа, и используй file_id из канала!"
        
        await message.answer(
            response_text,
            parse_mode="HTML"
        )
        logger.info("✅ Информация о file_id отправлена админу")
    else:
        logger.debug(f"Пользователь {message.from_user.id} отправил видео, но он не админ - игнорируем")


@router.message(F.photo)
async def photo_file_id_handler(message: Message, bot: Bot):
    """Обработчик для получения file_id фото (для админов) — для рассылок с фото"""
    if message.from_user.id not in Config.ADMIN_USER_IDS:
        return
    # Берём фото наибольшего размера
    photo = message.photo[-1]
    file_id = photo.file_id
    response_text = (
        f"🖼 <b>Photo file_id для рассылки</b>\n\n"
        f"<b>file_id:</b>\n<code>{file_id}</code>\n\n"
        f"💡 Вставьте этот file_id в поле «Photo file_id» в админке при создании рассылки — "
        f"сообщение уйдёт с этим фото и текстом подписью."
    )
    await message.answer(response_text, parse_mode="HTML")