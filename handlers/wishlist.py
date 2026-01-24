from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.main_menu import get_main_menu_keyboard
from keyboards.wishlist import get_wishlist_keyboard, get_wishlist_item_keyboard
from database.connection import Database
from messages import get_wishlist_intro, get_wishlist_select_item_text

router = Router()


@router.message(F.text == "🎁 Вишлист")
async def wishlist_handler(message: Message):
    """Обработчик раздела виш-листа"""
    items = await Database.fetch("""
        SELECT id,
               name,
               description,
               link,
               price_hint,
               is_taken,
               taken_by_user_id,
               ROW_NUMBER() OVER (ORDER BY is_taken, order_index, created_at) AS display_index
        FROM wishlist_items
        ORDER BY is_taken, order_index, created_at
    """)
    
    if not items:
        await message.answer(
            get_wishlist_intro(),
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    items_list = [dict(item) for item in items]
    await message.answer(
        f"{get_wishlist_intro()}\n\n{get_wishlist_select_item_text()}",
        reply_markup=get_wishlist_keyboard(items_list)
    )


@router.callback_query(F.data.startswith("wishlist_page_"))
async def wishlist_page_handler(callback: CallbackQuery):
    """Обработчик переключения страниц виш-листа"""
    page = int(callback.data.split("_")[-1])
    
    items = await Database.fetch("""
        SELECT id,
               name,
               description,
               link,
               price_hint,
               is_taken,
               taken_by_user_id,
               ROW_NUMBER() OVER (ORDER BY is_taken, order_index, created_at) AS display_index
        FROM wishlist_items
        ORDER BY is_taken, order_index, created_at
    """)
    
    items_list = [dict(item) for item in items]
    await callback.message.edit_text(
        f"{get_wishlist_intro()}\n\n{get_wishlist_select_item_text()}",
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
    
    status = "✅ Забрано" if item["is_taken"] else "🛒 Доступно"
    index = item.get("display_index")
    title = f"{index}. {item['name']}" if index is not None else item["name"]
    text = f"<b>{title}</b>\n\n"
    
    if item["description"]:
        text += f"<b>Комментарий:</b> {item['description']}\n\n"
    
    if item.get("price_hint"):
        text += f"<b>Ориентировочная стоимость:</b> {item['price_hint']}\n\n"
    
    if item["link"]:
        text += f"<b>Ссылка:</b> {item['link']}\n\n"
    
    text += f"<b>Статус:</b> {status}"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_wishlist_item_keyboard(item_id, item["is_taken"]),
        disable_web_page_preview=True,
        parse_mode="HTML"
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
    
    await callback.answer("Товар отмечен как забранный! ✅", show_alert=True)
    
    # Обновляем информацию о товаре
    updated_item = await Database.fetchrow("""
        SELECT *
        FROM (
            SELECT id,
                   name,
                   description,
                   link,
                   price_hint,
                   is_taken,
                   taken_by_user_id,
                   ROW_NUMBER() OVER (ORDER BY is_taken, order_index, created_at) AS display_index
            FROM wishlist_items
        ) wi
        WHERE wi.id = $1
    """, item_id)
    
    status = "✅ Забрано"
    index = updated_item.get("display_index")
    title = f"{index}. {updated_item['name']}" if index is not None else updated_item["name"]
    text = f"<b>{title}</b>\n\n"
    if updated_item["description"]:
        text += f"<b>Комментарий:</b> {updated_item['description']}\n\n"
    if updated_item.get("price_hint"):
        text += f"<b>Ориентировочная стоимость:</b> {updated_item['price_hint']}\n\n"
    if updated_item["link"]:
        text += f"<b>Ссылка:</b> {updated_item['link']}\n\n"
    text += f"<b>Статус:</b> {status}"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_wishlist_item_keyboard(item_id, True),
        disable_web_page_preview=True,
        parse_mode="HTML"
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
    
    await callback.answer("Отметка отменена", show_alert=True)
    
    # Обновляем информацию о товаре
    updated_item = await Database.fetchrow("""
        SELECT *
        FROM (
            SELECT id,
                   name,
                   description,
                   link,
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
        text += f"<b>Ориентировочная стоимость:</b> {updated_item['price_hint']}\n\n"
    if updated_item["link"]:
        text += f"<b>Ссылка:</b> {updated_item['link']}\n\n"
    text += f"<b>Статус:</b> {status}"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_wishlist_item_keyboard(item_id, False),
        disable_web_page_preview=True,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "wishlist_list")
async def wishlist_list_handler(callback: CallbackQuery):
    """Обработчик возврата к списку товаров"""
    items = await Database.fetch("""
        SELECT id,
               name,
               description,
               link,
               price_hint,
               is_taken,
               taken_by_user_id,
               ROW_NUMBER() OVER (ORDER BY is_taken, order_index, created_at) AS display_index
        FROM wishlist_items
        ORDER BY is_taken, order_index, created_at
    """)
    
    items_list = [dict(item) for item in items]
    await callback.message.edit_text(
        f"{get_wishlist_intro()}\n\n{get_wishlist_select_item_text()}",
        reply_markup=get_wishlist_keyboard(items_list)
    )
    await callback.answer()
