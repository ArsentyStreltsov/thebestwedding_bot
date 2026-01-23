from aiogram import Router, F
from aiogram.types import Message
from keyboards.main_menu import get_main_menu_keyboard
from messages import get_disclaimer_text

router = Router()


@router.message(F.text == "📋 Дисклеймер")
async def disclaimer_handler(message: Message):
    """Обработчик раздела дисклеймера"""
    await message.answer(
        get_disclaimer_text(),
        reply_markup=get_main_menu_keyboard()
    )
