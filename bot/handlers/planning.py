from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from datetime import date, datetime, timedelta
from db import TaskRepo, PlanRepo, StatsRepo, UserRepo
from ..keyboards.kb import get_plan_menu, get_back_button, get_settings_menu
from ai.scheduler import generate_day_plan

router = Router()


@router.message(F.text == "📊 План на сегодня")
@router.callback_query(F.data == "plan_generate")
async def show_today_plan(event: Message | CallbackQuery):
    user_id = event.from_user.id
    today = date.today().isoformat()
    
    existing_plan = await PlanRepo.get(user_id, today)
    
    if existing_plan:
        await show_plan(event, existing_plan.schedule)
        return
    
    tasks = await TaskRepo.get_user_tasks(user_id)
    user = await UserRepo.get(user_id)
    
    if not tasks:
        msg = event if isinstance(event, Message) else event.message
        text = "📭 Нет задач на сегодня. Добавь задачи, и я составлю план!"
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(text, reply_markup=get_plan_menu())
        else:
            await msg.answer(text, reply_markup=get_plan_menu())
        return
    
    plan_text = await generate_day_plan(tasks, user.timezone if user else "UTC")
    
    await PlanRepo.create(user_id, today, plan_text)
    await show_plan(event, plan_text)


async def show_plan(event: Message | CallbackQuery, plan_text: str):
    msg = event if isinstance(event, Message) else event.message
    text = f"📅 <b>План на сегодня</b>\n\n{plan_text}"
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=get_plan_menu())
    else:
        await msg.answer(text, reply_markup=get_plan_menu())


@router.message(F.text == "📈 Статистика")
async def show_stats(message: Message):
    user_id = message.from_user.id
    today = date.today()
    week_ago = today - timedelta(days=7)
    
    tasks = await TaskRepo.get_user_tasks(user_id, include_completed=True)
    completed = [t for t in tasks if t.status == "completed"]
    
    today_tasks = [t for t in tasks if t.deadline == today.isoformat()]
    today_completed = [t for t in completed if t.completed_at and 
                       t.completed_at.startswith(today.isoformat())]
    
    text = f"""📈 <b>Твоя статистика</b>

📊 Сегодня:
• Выполнено: {len(today_completed)}/{len(today_tasks)} задач
• Продуктивность: {len(today_completed)/max(len(today_tasks),1)*100:.0f}%

📅 За неделю:
• Всего задач: {len([t for t in tasks if t.created_at])}
• Выполнено: {len(completed)}

🏆 Топ категории:
"""
    
    categories = {}
    for t in completed:
        categories[t.category] = categories.get(t.category, 0) + 1
    
    if categories:
        top_cat = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
        for cat, count in top_cat:
            text += f"• {cat}: {count} задач\n"
    
    await message.answer(text)


@router.message(F.text == "⚙️ Настройки")
@router.callback_query(F.data == "settings")
async def show_settings(event: Message | CallbackQuery):
    msg = event if isinstance(event, Message) else event.message
    user = await UserRepo.get(event.from_user.id)
    
    text = f"""⚙️ <b>Настройки</b>

🌍 Часовой пояс: {user.timezone if user else 'UTC'}
🌅 Утренний план: {user.morning_time if user else '09:00'}
🌙 Вечерний отчёт: {user.evening_time if user else '21:00'}
"""
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=get_settings_menu())
    else:
        await msg.answer(text, reply_markup=get_settings_menu())
