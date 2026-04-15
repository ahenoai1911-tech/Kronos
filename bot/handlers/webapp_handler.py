from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, WebAppInfo
from datetime import datetime
import json
from db import TaskRepo, UserRepo
from core.config import settings
from ..keyboards.kb import get_back_button

router = Router()


@router.message(F.text == "📱 Приложение")
async def open_webapp(message: Message):
    if not settings.WEBAPP_URL:
        await message.answer(
            "⚠️ WebApp пока не настроен.\n"
            "Добавь WEBAPP_URL в .env файл"
        )
        return
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📱 Открыть Kronos App",
            web_app=WebAppInfo(url=settings.WEBAPP_URL)
        )]
    ])
    
    await message.answer(
        "📱 <b>Kronos WebApp</b>\n\n"
        "Удобный интерфейс для управления задачами",
        reply_markup=kb
    )


@router.message(F.web_app_data)
async def handle_webapp_data(message: Message):
    data = json.loads(message.web_app_data.data)
    action = data.get("action")
    
    if action == "add_task":
        task = await TaskRepo.create(
            user_id=message.from_user.id,
            title=data.get("title"),
            description=data.get("description"),
            category=data.get("category", "general"),
            priority=data.get("priority", 2),
            deadline=data.get("deadline"),
            estimated_minutes=data.get("estimated_minutes")
        )
        await message.answer(f"✅ Задача создана: {task.title}")
    
    elif action == "complete_task":
        task_id = data.get("task_id")
        task = await TaskRepo.complete(task_id)
        if task:
            await message.answer(f"✅ Выполнено: {task.title}")
    
    elif action == "delete_task":
        task_id = data.get("task_id")
        await TaskRepo.delete(task_id)
        await message.answer("🗑 Задача удалена")
    
    elif action == "update_task":
        task = await TaskRepo.update(
            task_id=data.get("task_id"),
            title=data.get("title"),
            description=data.get("description"),
            priority=data.get("priority"),
            category=data.get("category"),
            deadline=data.get("deadline"),
            status=data.get("status")
        )
        await message.answer(f"✏️ Задача обновлена: {task.title}")


@router.callback_query(F.data == "settings_timezone")
async def change_timezone(callback: CallbackQuery):
    await callback.message.edit_text(
        "🌍 Напиши название города для часового пояса:\n\n"
        "Примеры: Moscow, London, New York, Tokyo",
        reply_markup=get_back_button()
    )
    await callback.answer()


@router.message(F.text.regexp(r"^[A-Za-zА-Яа-я\s]+$"))
async def set_timezone(message: Message):
    from .start import get_timezone_by_city
    from aiogram.fsm.context import FSMContext
    
    timezone = get_timezone_by_city(message.text)
    await UserRepo.update_settings(message.from_user.id, timezone=timezone)
    
    await message.answer(f"✅ Часовой пояс изменен на: {timezone}")
