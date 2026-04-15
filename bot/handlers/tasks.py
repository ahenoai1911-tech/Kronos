from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
from db import TaskRepo
from ..keyboards.kb import (
    get_tasks_menu, get_task_actions, get_priority_keyboard,
    get_category_keyboard, get_back_button
)
from ai.parser import parse_task_text

router = Router()


class TaskStates(StatesGroup):
    waiting_title = State()
    waiting_description = State()
    waiting_deadline = State()
    waiting_priority = State()
    waiting_category = State()


@router.message(F.text == "📋 Задачи")
async def show_tasks_menu(message: Message):
    await message.answer("📋 Управление задачами", reply_markup=get_tasks_menu())


@router.callback_query(F.data == "task_list")
async def show_task_list(callback: CallbackQuery):
    tasks = await TaskRepo.get_user_tasks(callback.from_user.id)
    
    if not tasks:
        await callback.message.edit_text(
            "📭 У тебя пока нет задач. Добавь первую!",
            reply_markup=get_tasks_menu()
        )
        return
    
    text = "📋 <b>Твои задачи:</b>\n\n"
    for task in tasks:
        priority_emoji = {1: "🔴", 2: "🟡", 3: "🟢"}.get(task.priority, "⚪")
        deadline = f" 📅 {task.deadline}" if task.deadline else ""
        text += f"{priority_emoji} <b>{task.title}</b>{deadline}\n"
        text += f"   📁 {task.category} | ID: {task.id}\n"
    
    await callback.message.edit_text(text, reply_markup=get_tasks_actions_list(tasks))


def get_tasks_actions_list(tasks) -> object:
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    for task in tasks[:10]:
        buttons.append([
            InlineKeyboardButton(
                text=f"{task.title[:30]}",
                callback_data=f"task_view_{task.id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data.startswith("task_view_"))
async def view_task(callback: CallbackQuery):
    task_id = int(callback.data.split("_")[-1])
    task = await TaskRepo.get(task_id)
    
    if not task:
        await callback.answer("Задача не найдена")
        return
    
    priority_names = {1: "Высокий", 2: "Средний", 3: "Низкий"}
    text = f"""📋 <b>{task.title}</b>

📝 Описание: {task.description or 'не указано'}
📁 Категория: {task.category}
⚡ Приоритет: {priority_names.get(task.priority, 'Средний')}
📅 Дедлайн: {task.deadline or 'не указан'}
⏱ Оценка: {f'{task.estimated_minutes} мин' if task.estimated_minutes else 'не указана'}
"""
    
    await callback.message.edit_text(text, reply_markup=get_task_actions(task_id))


@router.callback_query(F.data == "task_add")
async def add_task_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "✍️ Напиши задачу в свободной форме.\n\n"
        "Примеры:\n"
        "• «Завтра в 15:00 встреча с клиентом»\n"
        "• «До пятницы подготовить отчёт по проекту»\n"
        "• «Позвонить маме вечером»\n\n"
        "AI автоматически определит дату и приоритет.",
        reply_markup=get_back_button()
    )
    await state.set_state(TaskStates.waiting_title)


@router.message(TaskStates.waiting_title)
async def process_task_title(message: Message, state: FSMContext):
    parsed = await parse_task_text(message.text)
    
    await state.update_data(
        title=parsed.get("title", message.text),
        deadline=parsed.get("deadline"),
        priority=parsed.get("priority", 2),
        category=parsed.get("category", "general"),
        estimated_minutes=parsed.get("estimated_minutes"),
        description=parsed.get("description")
    )
    
    await message.answer(
        f"📝 Задача: <b>{parsed.get('title', message.text)}</b>\n\n"
        "Добавить описание? Или нажми /skip чтобы пропустить."
    )
    await state.set_state(TaskStates.waiting_description)


@router.message(TaskStates.waiting_description)
async def process_task_description(message: Message, state: FSMContext):
    if message.text != "/skip":
        await state.update_data(description=message.text)
    await state.set_state(TaskStates.waiting_priority)
    await message.answer("⚡ Выбери приоритет:", reply_markup=get_priority_keyboard())


@router.callback_query(F.data.startswith("priority_"), TaskStates.waiting_priority)
async def process_priority(callback: CallbackQuery, state: FSMContext):
    priority = int(callback.data.split("_")[-1])
    await state.update_data(priority=priority)
    await state.set_state(TaskStates.waiting_category)
    await callback.message.edit_text("📁 Выбери категорию:", reply_markup=get_category_keyboard())


@router.callback_query(F.data.startswith("category_"), TaskStates.waiting_category)
async def process_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split("_")[-1]
    data = await state.get_data()
    
    task = await TaskRepo.create(
        user_id=callback.from_user.id,
        title=data["title"],
        description=data.get("description"),
        category=category,
        priority=data.get("priority", 2),
        deadline=data.get("deadline"),
        estimated_minutes=data.get("estimated_minutes")
    )
    
    await state.clear()
    await callback.message.edit_text(
        f"✅ Задача создана!\n\n"
        f"📋 <b>{task.title}</b>\n"
        f"📁 {category} | ⚡ Приоритет: {task.priority}",
        reply_markup=get_tasks_menu()
    )


@router.callback_query(F.data.startswith("task_done_"))
async def complete_task(callback: CallbackQuery):
    task_id = int(callback.data.split("_")[-1])
    task = await TaskRepo.complete(task_id)
    
    if task:
        await callback.answer("✅ Задача выполнена!")
        await callback.message.delete()
    else:
        await callback.answer("Задача не найдена")


@router.callback_query(F.data.startswith("task_del_"))
async def delete_task(callback: CallbackQuery):
    task_id = int(callback.data.split("_")[-1])
    await TaskRepo.delete(task_id)
    await callback.answer("🗑 Задача удалена")
    await callback.message.delete()


@router.callback_query(F.data == "task_completed")
async def show_completed_tasks(callback: CallbackQuery):
    tasks = await TaskRepo.get_user_tasks(callback.from_user.id, include_completed=True)
    tasks = [t for t in tasks if t.status == "completed"]
    
    if not tasks:
        await callback.answer("Нет выполненных задач")
        return
    
    text = "✅ <b>Выполненные задачи:</b>\n\n"
    for task in tasks[-10:]:
        text += f"✓ {task.title}\n"
    
    await callback.message.edit_text(text, reply_markup=get_back_button())
