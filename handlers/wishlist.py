from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from keyboards.main_menu import get_main_menu_keyboard
from keyboards.wishlist import get_wishlist_keyboard, get_wishlist_item_keyboard
from database.connection import Database

router = Router()


@router.message(F.text == "🎁 Виш-лист")
async def wishlist_handler(message: Message):
    """Обработчик раздела виш-листа"""
    items = await Database.fetch("""
        SELECT id, name, description, link, is_taken, taken_by_user_id
        FROM wishlist_items
        ORDER BY created_at DESC
    """)
    
    if not items:
        await message.answer(
            "Виш-лист пока пуст. Скоро здесь появятся подарки! 🎁",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    items_list = [dict(item) for item in items]
    await message.answer(
        "🎁 Виш-лист подарков:\n\n"
        "Выбери товар, чтобы посмотреть подробности или отметить его:",
        reply_markup=get_wishlist_keyboard(items_list)
    )


@router.callback_query(F.data.startswith("wishlist_page_"))
async def wishlist_page_handler(callback: CallbackQuery):
    """Обработчик переключения страниц виш-листа"""
    page = int(callback.data.split("_")[-1])
    
    items = await Database.fetch("""
        SELECT id, name, description, link, is_taken, taken_by_user_id
        FROM wishlist_items
        ORDER BY created_at DESC
    """)
    
    items_list = [dict(item) for item in items]
    await callback.message.edit_text(
        "🎁 Виш-лист подарков:\n\n"
        "Выбери товар, чтобы посмотреть подробности или отметить его:",
        reply_markup=get_wishlist_keyboard(items_list, page=page)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("wishlist_item_"))
async def wishlist_item_handler(callback: CallbackQuery):
    """Обработчик просмотра конкретного товара"""
    item_id = int(callback.data.split("_")[-1])
    
    item = await Database.fetchrow("""
        SELECT id, name, description, link, is_taken, taken_by_user_id
        FROM wishlist_items
        WHERE id = $1
    """, item_id)
    
    if not item:
        await callback.answer("Товар не найден", show_alert=True)
        return
    
    status = "✅ Забрано" if item["is_taken"] else "🛒 Доступно"
    text = f"🎁 {item['name']}\n\n"
    
    if item["description"]:
        text += f"{item['description']}\n\n"
    
    text += f"Статус: {status}\n"
    
    if item["link"]:
        text += f"Ссылка: {item['link']}"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_wishlist_item_keyboard(item_id, item["is_taken"]),
        disable_web_page_preview=False
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
        SELECT id, name, description, link, is_taken
        FROM wishlist_items
        WHERE id = $1
    """, item_id)
    
    status = "✅ Забрано"
    text = f"🎁 {updated_item['name']}\n\n"
    if updated_item["description"]:
        text += f"{updated_item['description']}\n\n"
    text += f"Статус: {status}\n"
    if updated_item["link"]:
        text += f"Ссылка: {updated_item['link']}"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_wishlist_item_keyboard(item_id, True),
        disable_web_page_preview=False
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
        SELECT id, name, description, link, is_taken
        FROM wishlist_items
        WHERE id = $1
    """, item_id)
    
    status = "🛒 Доступно"
    text = f"🎁 {updated_item['name']}\n\n"
    if updated_item["description"]:
        text += f"{updated_item['description']}\n\n"
    text += f"Статус: {status}\n"
    if updated_item["link"]:
        text += f"Ссылка: {updated_item['link']}"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_wishlist_item_keyboard(item_id, False),
        disable_web_page_preview=False
    )


@router.callback_query(F.data == "wishlist_list")
async def wishlist_list_handler(callback: CallbackQuery):
    """Обработчик возврата к списку товаров"""
    items = await Database.fetch("""
        SELECT id, name, description, link, is_taken, taken_by_user_id
        FROM wishlist_items
        ORDER BY created_at DESC
    """)
    
    items_list = [dict(item) for item in items]
    await callback.message.edit_text(
        "🎁 Виш-лист подарков:\n\n"
        "Выбери товар, чтобы посмотреть подробности или отметить его:",
        reply_markup=get_wishlist_keyboard(items_list)
    )
    await callback.answer()
