from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional


def get_wishlist_keyboard(items: list[dict], page: int = 0, items_per_page: int = 5) -> InlineKeyboardMarkup:
    """Клавиатура для списка товаров виш-листа"""
    keyboard_buttons = []
    
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_items = items[start_idx:end_idx]
    
    for item in page_items:
        # Порядковый номер по всему списку
        index = item.get("display_index")
        if item.get("is_taken"):
            # Для уже занятых показываем зелёную галочку вместо номера
            button_text = f"✅ {item.get('name', 'Без названия')}"
        else:
            number_prefix = f"{index}. " if index is not None else ""
            button_text = f"{number_prefix}{item.get('name', 'Без названия')}"
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"wishlist_item_{item['id']}"
            )
        ])
    
    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="◀️ Назад", callback_data=f"wishlist_page_{page - 1}")
        )
    if end_idx < len(items):
        nav_buttons.append(
            InlineKeyboardButton(text="Вперед ▶️", callback_data=f"wishlist_page_{page + 1}")
        )
    
    if nav_buttons:
        keyboard_buttons.append(nav_buttons)
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def get_wishlist_item_keyboard(item_id: int, is_taken: bool) -> InlineKeyboardMarkup:
    """Клавиатура для конкретного товара виш-листа"""
    keyboard_buttons = []
    
    if not is_taken:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text="✅ Отметить как забранное",
                callback_data=f"wishlist_take_{item_id}"
            )
        ])
    else:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text="❌ Отменить отметку",
                callback_data=f"wishlist_untake_{item_id}"
            )
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 К списку", callback_data="wishlist_list")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
