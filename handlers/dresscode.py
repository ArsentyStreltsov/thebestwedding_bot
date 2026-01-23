from aiogram import Router, F
from aiogram.types import Message
from keyboards.main_menu import get_main_menu_keyboard
from messages import get_dresscode_text

router = Router()


@router.message(F.text == "👰‍♀️ Дресс-код")
async def dresscode_handler(message: Message):
    """Обработчик раздела дресс-кода"""
    await message.answer(
        get_dresscode_text(),
        reply_markup=get_main_menu_keyboard()
    )
