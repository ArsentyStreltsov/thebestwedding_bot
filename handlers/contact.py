from aiogram import Router, F
from aiogram.types import Message
from keyboards.main_menu import get_main_menu_keyboard

router = Router()


@router.message(F.text == "📞 Связаться с нами")
async def contact_handler(message: Message):
    """Обработчик раздела связи с организаторами"""
    contact_text = (
        "📞 Связаться с нами\n\n"
        "Если у тебя есть вопросы или предложения, "
        "ты всегда можешь написать нам напрямую в личные сообщения.\n\n"
        "Мы будем рады ответить на все твои вопросы! 💬"
    )
    
    await message.answer(
        contact_text,
        reply_markup=get_main_menu_keyboard()
    )
