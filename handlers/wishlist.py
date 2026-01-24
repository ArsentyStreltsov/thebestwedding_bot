from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional
from html import escape
from keyboards.main_menu import get_main_menu_keyboard
from keyboards.wishlist import get_wishlist_keyboard, get_wishlist_item_keyboard
from database.connection import Database
from messages import (
    get_wishlist_intro,
    get_wishlist_select_item_text,
    get_wishlist_how_it_works_text,
    get_wishlist_logistics_text,
    get_wishlist_empty_text,
)

router = Router()


def _format_price_hint(raw: Optional[str]) -> str:
    """
    Возвращает стоимость как текст (без автоматического добавления ₽),
    но слегка модифицирует её, чтобы Telegram не подсвечивал как номер/телефон.
    """
    if not raw:
        return ""
    value = str(raw).strip()
    # Заменяем обычный дефис на похожий символ, чтобы Telegram не воспринимал как номер телефона
    value = value.replace("-", "−")
    return value


def _format_link(link: Optional[str]) -> str:
    """Форматирование ссылки: обрезаем длинные и делаем кликабельными."""
    if not link:
        return ""
    link = link.strip()
    display = link
    if len(display) > 50:
        display = display[:47] + "..."
    # Экранируем текст и ссылку для HTML
    return f'<a href="{escape(link)}">{escape(display)}</a>'


def _format_links_block(link: Optional[str], link2: Optional[str]) -> str:
    """
    Формирует HTML-блок со ссылками для карточки товара.
    Поддерживает одну или две ссылки.
    """
    links: list[str] = []
    if link:
        links.append(_format_link(link))
    if link2:
        links.append(_format_link(link2))
    if not links:
        return ""
    if len(links) == 1:
        return f"<b>Ссылка:</b> {links[0]}\n\n"
    # две ссылки
    numbered = [f"{idx + 1}) {l}" for idx, l in enumerate(links)]
    return "<b>Ссылки:</b>\n" + "\n".join(numbered) + "\n\n"

@router.message(F.text == "🎁 Вишлист")
async def wishlist_handler(message: Message):
    """Обработчик раздела виш-листа (первый экран с двумя кнопками)"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 Открыть вишлист",
                    callback_data="wishlist_open",
                )
            ],
            [
                InlineKeyboardButton(
                    text="✈️ Информация по логистике",
                    callback_data="wishlist_logistics",
                )
            ],
        ]
    )
    await message.answer(
        get_wishlist_intro(),
        reply_markup=keyboard,
    )


@router.callback_query(F.data == "wishlist_open")
async def wishlist_open_handler(callback: CallbackQuery):
    """Открытие списка подарков с объяснением, как работает вишлист"""
    items = await Database.fetch(
        """
        SELECT id,
               name,
               description,
               link,
               link2,
               price_hint,
               is_taken,
               taken_by_user_id,
               ROW_NUMBER() OVER (ORDER BY is_taken, order_index, created_at) AS display_index
        FROM wishlist_items
        ORDER BY is_taken, order_index, created_at
        """
    )

    if not items:
        await callback.message.edit_text(
            get_wishlist_empty_text(),
            reply_markup=get_main_menu_keyboard(),
        )
        await callback.answer()
        return

    items_list = [dict(item) for item in items]
    await callback.message.edit_text(
        get_wishlist_how_it_works_text(),
        reply_markup=get_wishlist_keyboard(items_list),
        disable_web_page_preview=True,
    )
    await callback.answer()


@router.callback_query(F.data == "wishlist_logistics")
async def wishlist_logistics_handler(callback: CallbackQuery):
    """Пояснение по логистике подарков"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="wishlist_back_to_intro",
                )
            ],
        ]
    )
    await callback.message.edit_text(
        get_wishlist_logistics_text(),
        reply_markup=keyboard,
        disable_web_page_preview=True,
    )
    await callback.answer()


@router.callback_query(F.data == "wishlist_back_to_intro")
async def wishlist_back_to_intro_handler(callback: CallbackQuery):
    """Возврат с логистики к первому экрану вишлиста"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 Открыть вишлист",
                    callback_data="wishlist_open",
                )
            ],
            [
                InlineKeyboardButton(
                    text="✈️ Информация по логистике",
                    callback_data="wishlist_logistics",
                )
            ],
        ]
    )
    await callback.message.edit_text(
        get_wishlist_intro(),
        reply_markup=keyboard,
    )
    await callback.answer()

@router.callback_query(F.data.startswith("wishlist_page_"))
async def wishlist_page_handler(callback: CallbackQuery):
    """Обработчик переключения страниц виш-листа"""
    page = int(callback.data.split("_")[-1])
    
    items = await Database.fetch("""
        SELECT id,
               name,
               description,
               link,
               link2,
               price_hint,
               is_taken,
               taken_by_user_id,
               ROW_NUMBER() OVER (ORDER BY is_taken, order_index, created_at) AS display_index
        FROM wishlist_items
        ORDER BY is_taken, order_index, created_at
    """)
    
    items_list = [dict(item) for item in items]
    await callback.message.edit_text(
        get_wishlist_how_it_works_text(),
        reply_markup=get_wishlist_keyboard(items_list, page=page)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("wishlist_item_"))
async def wishlist_item_handler(callback: CallbackQuery):
    """Обработчик просмотра конкретного товара"""
    item_id = int(callback.data.split("_")[-1])
    
    item = await Database.fetchrow("""
        SELECT *
        FROM (
            SELECT id,
                   name,
                   description,
                   link,
                   link2,
                   price_hint,
                   is_taken,
                   taken_by_user_id,
                   ROW_NUMBER() OVER (ORDER BY is_taken, order_index, created_at) AS display_index
            FROM wishlist_items
        ) wi
        WHERE wi.id = $1
    """, item_id)
    
    if not item:
        await callback.answer("Товар не найден", show_alert=True)
        return

    user_id = callback.from_user.id
    is_taken = item["is_taken"]
    taken_by = item.get("taken_by_user_id")
    can_untake = bool(is_taken and taken_by == user_id)

    status = "✅ Этот подарок кто-то уже выбрал" if is_taken else "🛒 Доступно"
    index = item.get("display_index")
    title = f"{index}. {item['name']}" if index is not None else item["name"]
    text = f"<b>{title}</b>\n\n"
    
    if item["description"]:
        text += f"<b>Комментарий:</b> {item['description']}\n\n"
    
    if item.get("price_hint"):
        text += f"<b>Стоимость:</b> {_format_price_hint(item['price_hint'])}\n\n"
    links_block = _format_links_block(item.get("link"), item.get("link2"))
    if links_block:
        text += links_block
    
    text += f"<b>Статус:</b> {status}"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_wishlist_item_keyboard(item_id, is_taken, can_untake),
        disable_web_page_preview=True,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("wishlist_take_"))
async def wishlist_take_handler(callback: CallbackQuery):
    """Обработчик отметки товара как забранного"""
    item_id = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id
    
    # Проверяем, не забран ли уже товар
    item = await Database.fetchrow("""
        SELECT is_taken FROM wishlist_items WHERE id = $1
    """, item_id)
    
    if item and item["is_taken"]:
        await callback.answer("Этот товар уже забран!", show_alert=True)
        return
    
    await Database.execute("""
        UPDATE wishlist_items
        SET is_taken = TRUE, taken_by_user_id = $1, updated_at = CURRENT_TIMESTAMP
        WHERE id = $2
    """, user_id, item_id)
    
    # Краткое уведомление без модального окна
    await callback.answer("✅ Вы выбрали этот подарок!")
    
    # Обновляем информацию о товаре
    updated_item = await Database.fetchrow("""
        SELECT *
        FROM (
            SELECT id,
                   name,
                   description,
                   link,
                   link2,
                   price_hint,
                   is_taken,
                   taken_by_user_id,
                   ROW_NUMBER() OVER (ORDER BY is_taken, order_index, created_at) AS display_index
            FROM wishlist_items
        ) wi
        WHERE wi.id = $1
    """, item_id)
    
    status = "✅ Этот подарок кто-то уже выбрал"
    index = updated_item.get("display_index")
    title = f"{index}. {updated_item['name']}" if index is not None else updated_item["name"]
    text = f"<b>{title}</b>\n\n"
    if updated_item["description"]:
        text += f"<b>Комментарий:</b> {updated_item['description']}\n\n"
    if updated_item.get("price_hint"):
        text += f"<b>Стоимость:</b> {_format_price_hint(updated_item['price_hint'])}\n\n"
    links_block = _format_links_block(updated_item.get("link"), updated_item.get("link2"))
    if links_block:
        text += links_block
    text += f"<b>Статус:</b> {status}"
    
    await callback.message.edit_text(
        text,
        # Этот пользователь только что выбрал подарок — даём возможность отменить
        reply_markup=get_wishlist_item_keyboard(item_id, True, can_untake=True),
        disable_web_page_preview=True,
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("wishlist_untake_"))
async def wishlist_untake_handler(callback: CallbackQuery):
    """Обработчик отмены отметки товара"""
    item_id = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id
    
    # Проверяем, что товар был забран именно этим пользователем
    item = await Database.fetchrow("""
        SELECT taken_by_user_id FROM wishlist_items WHERE id = $1
    """, item_id)
    
    if not item or item["taken_by_user_id"] != user_id:
        await callback.answer("Вы не можете отменить эту отметку", show_alert=True)
        return
    
    await Database.execute("""
        UPDATE wishlist_items
        SET is_taken = FALSE, taken_by_user_id = NULL, updated_at = CURRENT_TIMESTAMP
        WHERE id = $1
    """, item_id)
    
    # Краткое уведомление без модального окна
    await callback.answer("Вы отменили выбор этого подарка")
    
    # Обновляем информацию о товаре
    updated_item = await Database.fetchrow("""
        SELECT *
        FROM (
            SELECT id,
                   name,
                   description,
                   link,
                   link2,
                   price_hint,
                   is_taken,
                   taken_by_user_id,
                   ROW_NUMBER() OVER (ORDER BY is_taken, order_index, created_at) AS display_index
            FROM wishlist_items
        ) wi
        WHERE wi.id = $1
    """, item_id)
    
    status = "🛒 Доступно"
    index = updated_item.get("display_index")
    title = f"{index}. {updated_item['name']}" if index is not None else updated_item["name"]
    text = f"<b>{title}</b>\n\n"
    if updated_item["description"]:
        text += f"<b>Комментарий:</b> {updated_item['description']}\n\n"
    if updated_item.get("price_hint"):
        text += f"<b>Стоимость:</b> {_format_price_hint(updated_item['price_hint'])}\n\n"
    links_block = _format_links_block(updated_item.get("link"), updated_item.get("link2"))
    if links_block:
        text += links_block
    text += f"<b>Статус:</b> {status}"
    
    await callback.message.edit_text(
        text,
        # Подарок снова свободен — показываем кнопку выбора
        reply_markup=get_wishlist_item_keyboard(item_id, False, can_untake=False),
        disable_web_page_preview=True,
        parse_mode="HTML",
    )


@router.callback_query(F.data == "wishlist_list")
async def wishlist_list_handler(callback: CallbackQuery):
    """Обработчик возврата к списку товаров"""
    items = await Database.fetch("""
        SELECT id,
               name,
               description,
               link,
               link2,
               price_hint,
               is_taken,
               taken_by_user_id,
               ROW_NUMBER() OVER (ORDER BY is_taken, order_index, created_at) AS display_index
        FROM wishlist_items
        ORDER BY is_taken, order_index, created_at
    """)
    
    items_list = [dict(item) for item in items]
    await callback.message.edit_text(
        get_wishlist_how_it_works_text(),
        reply_markup=get_wishlist_keyboard(items_list)
    )
    await callback.answer()
