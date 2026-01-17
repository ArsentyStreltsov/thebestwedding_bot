from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.main_menu import get_main_menu_keyboard
from keyboards.info import get_info_keyboard
from database.connection import Database

router = Router()


@router.message(F.text == "ℹ️ Полезная информация")
async def info_handler(message: Message):
    """Обработчик раздела полезной информации"""
    sections = await Database.fetch("""
        SELECT id, section, title, content, order_index
        FROM wedding_info
        ORDER BY order_index ASC, created_at ASC
    """)
    
    if not sections:
        await message.answer(
            "Информация пока не добавлена. Скоро здесь появится вся важная информация! 📋",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    sections_list = [dict(section) for section in sections]
    await message.answer(
        "ℹ️ Полезная информация о свадьбе:\n\n"
        "Выбери раздел, чтобы узнать подробности:",
        reply_markup=get_info_keyboard(sections_list)
    )


@router.callback_query(F.data.startswith("info_section_"))
async def info_section_handler(callback: CallbackQuery):
    """Обработчик просмотра конкретного раздела информации"""
    section_id = int(callback.data.split("_")[-1])
    
    section = await Database.fetchrow("""
        SELECT id, section, title, content
        FROM wedding_info
        WHERE id = $1
    """, section_id)
    
    if not section:
        await callback.answer("Раздел не найден", show_alert=True)
        return
    
    text = f"📋 {section['title']}\n\n{section['content']}"
    
    keyboard_buttons = [[
        InlineKeyboardButton(text="🔙 К разделам", callback_data="info_list"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    ]]
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    )
    await callback.answer()


@router.callback_query(F.data == "info_list")
async def info_list_handler(callback: CallbackQuery):
    """Обработчик возврата к списку разделов"""
    sections = await Database.fetch("""
        SELECT id, section, title, content, order_index
        FROM wedding_info
        ORDER BY order_index ASC, created_at ASC
    """)
    
    sections_list = [dict(section) for section in sections]
    await callback.message.edit_text(
        "ℹ️ Полезная информация о свадьбе:\n\n"
        "Выбери раздел, чтобы узнать подробности:",
        reply_markup=get_info_keyboard(sections_list)
    )
    await callback.answer()
