from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from keyboards.main_menu import get_main_menu_keyboard
from messages import get_info_text, get_google_calendar_url, get_apple_calendar_url, generate_ics_content

router = Router()


@router.message(F.text == "💍 Информация о свадьбе")
async def info_handler(message: Message):
    """Обработчик раздела информации о свадьбе"""
    # Получаем URL для календарей
    apple_calendar_url = get_apple_calendar_url()
    google_calendar_url = get_google_calendar_url()
    
    # Создаём inline-кнопки для добавления в календарь
    buttons = []
    
    # Добавляем кнопку Apple Calendar только если URL установлен
    if apple_calendar_url and apple_calendar_url.strip():
        buttons.append(
            InlineKeyboardButton(
                text="📱 Apple Calendar",
                url=apple_calendar_url
            )
        )
    
    # Добавляем кнопку Google Calendar
    buttons.append(
        InlineKeyboardButton(
            text="📅 Google Calendar",
            url=google_calendar_url
        )
    )
    
    # Создаём клавиатуру только если есть кнопки
    calendar_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[buttons] if buttons else []
    )
    
    # Отправляем текст с кнопками
    await message.answer(
        get_info_text(),
        reply_markup=calendar_keyboard,
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    
    # Отправляем .ics файл для Apple Calendar
    ics_content = generate_ics_content()
    ics_file = BufferedInputFile(
        ics_content.encode('utf-8'),
        filename="wedding.ics"
    )
    await message.answer_document(
        ics_file,
        caption="📅 Добавьте событие в календарь"
    )
