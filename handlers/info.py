from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.main_menu import get_main_menu_keyboard
from messages import get_info_text, get_google_calendar_url

router = Router()


@router.message(F.text == "💍 Информация о свадьбе")
async def info_handler(message: Message):
    """Обработчик раздела информации о свадьбе"""
    google_calendar_url = get_google_calendar_url()
    calendar_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="📅 Google Calendar", url=google_calendar_url)
        ]]
    )
    await message.answer(
        get_info_text(),
        reply_markup=calendar_keyboard,
        parse_mode="HTML",
        disable_web_page_preview=True
    )
