from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню бота"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💍 Информация о свадьбе"), KeyboardButton(text="👰‍♀️ Дресс-код")],
            [KeyboardButton(text="🎁 Вишлист"), KeyboardButton(text="📋 Дисклеймер")],
            [KeyboardButton(text="🎥 Видео-приглашение"), KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел из меню"
    )
    return keyboard
