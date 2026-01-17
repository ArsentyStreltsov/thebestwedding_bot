from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from keyboards.main_menu import get_main_menu_keyboard
from database.connection import Database

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user = message.from_user
    
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
    
    welcome_text = (
        f"Привет, {user.first_name}! 👋\n\n"
        "Добро пожаловать на нашу свадьбу! 🎉\n\n"
        "Здесь ты можешь найти всю полезную информацию о нашем торжестве, "
        "посмотреть виш-лист и связаться с нами.\n\n"
        "Выбери раздел из меню ниже:"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard()
    )


@router.message(F.text == "🔙 Главное меню")
async def main_menu_handler(message: Message):
    """Обработчик возврата в главное меню"""
    await message.answer(
        "Выбери раздел из меню:",
        reply_markup=get_main_menu_keyboard()
    )


@router.callback_query(F.data == "main_menu")
async def main_menu_callback_handler(callback: CallbackQuery):
    """Обработчик возврата в главное меню через callback"""
    await callback.message.answer(
        "Выбери раздел из меню:",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()
