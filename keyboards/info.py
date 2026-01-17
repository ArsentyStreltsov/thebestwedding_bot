from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional


def get_info_keyboard(sections: list[dict]) -> InlineKeyboardMarkup:
    """Клавиатура для разделов полезной информации"""
    keyboard_buttons = []
    
    for section in sections:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=section.get("title", "Без названия"),
                callback_data=f"info_section_{section['id']}"
            )
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
