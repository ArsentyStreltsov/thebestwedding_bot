from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional


def get_wishlist_keyboard(items: list[dict], page: int = 0, items_per_page: int = 5) -> InlineKeyboardMarkup:
    """Клавиатура для списка товаров виш-листа"""
    keyboard_buttons = []
    
    # Показываем все товары сразу, без пагинации
    for item in items:
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
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data="wishlist_back_to_intro")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def get_wishlist_item_keyboard(
    item_id: int,
    is_taken: bool,
    can_untake: bool = False,
) -> InlineKeyboardMarkup:
    """
    Клавиатура для конкретного товара виш-листа.
    
    - Если подарок свободен — показываем кнопку выбора.
    - Если подарок уже выбран и это сделал текущий пользователь (can_untake=True),
      показываем кнопку «Отменить выбор».
    - Если подарок выбран кем-то другим — никаких кнопок выбора/отмены не показываем.
    """
    keyboard_buttons = []

    if not is_taken:
        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    text="✅ Выбрать этот подарок",
                    callback_data=f"wishlist_take_{item_id}",
                )
            ]
        )
    elif can_untake:
        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    text="❌ Отменить выбор",
                    callback_data=f"wishlist_untake_{item_id}",
                )
            ]
        )

    keyboard_buttons.append(
        [InlineKeyboardButton(text="🔙 К списку", callback_data="wishlist_list")]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
