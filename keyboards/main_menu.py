from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню бота"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎁 Виш-лист")],
            [KeyboardButton(text="ℹ️ Полезная информация")],
            [KeyboardButton(text="📞 Связаться с нами")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел из меню"
    )
    return keyboard
