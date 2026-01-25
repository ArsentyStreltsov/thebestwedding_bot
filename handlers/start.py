import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from keyboards.main_menu import get_main_menu_keyboard
from database.connection import Database
from messages import get_welcome_message
from utils.telegram_logger import send_to_logs_group
from config import Config

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user = message.from_user
    
    # Проверяем, новый ли это пользователь
    existing_user = await Database.fetchrow(
        "SELECT user_id FROM users WHERE user_id = $1",
        user.id
    )
    is_new_user = existing_user is None
    
    # Сохранение/обновление пользователя в БД
    await Database.execute("""
        INSERT INTO users (user_id, username, first_name, last_name)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (user_id) 
        DO UPDATE SET 
            username = EXCLUDED.username,
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            updated_at = CURRENT_TIMESTAMP
    """, user.id, user.username, user.first_name, user.last_name)
    
    # Если новый пользователь - логируем и отправляем в группу
    if is_new_user:
        # Получаем общее количество пользователей
        total_users = await Database.fetchval("SELECT COUNT(*) FROM users")
        
        user_info = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Без имени"
        username_info = f"@{user.username}" if user.username else "без username"
        
        log_message = (
            f"👤 <b>Новый пользователь!</b>\n\n"
            f"Имя: {user_info}\n"
            f"Username: {username_info}\n"
            f"ID: <code>{user.id}</code>\n\n"
            f"📊 Всего пользователей: <b>{total_users}</b>"
        )
        
        logger.info(f"Новый пользователь: {user_info} (@{user.username or 'нет'}, ID: {user.id}). Всего: {total_users}")
        
        # Отправляем в группу
        if Config.LOGS_GROUP_ID:
            logger.info(f"Попытка отправить уведомление в группу {Config.LOGS_GROUP_ID}")
            try:
                result = await send_to_logs_group(log_message)
                if result:
                    logger.info("✅ Уведомление о новом пользователе успешно отправлено в группу")
                else:
                    logger.warning("❌ Не удалось отправить уведомление о новом пользователе в группу")
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления о новом пользователе: {e}", exc_info=True)
        else:
            logger.warning("LOGS_GROUP_ID не установлен, пропускаем отправку уведомления")
    
    await message.answer(
        get_welcome_message(user.first_name or "друг"),
        reply_markup=get_main_menu_keyboard()
    )


@router.message(F.text == "🏠 Главное меню")
async def main_menu_handler(message: Message):
    """Обработчик возврата в главное меню"""
    user = message.from_user
    
    await message.answer(
        get_welcome_message(user.first_name or "друг"),
        reply_markup=get_main_menu_keyboard()
    )


@router.callback_query(F.data == "main_menu")
async def main_menu_callback_handler(callback: CallbackQuery):
    """Обработчик возврата в главное меню через callback"""
    user = callback.from_user
    
    await callback.message.answer(
        get_welcome_message(user.first_name or "друг"),
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()
