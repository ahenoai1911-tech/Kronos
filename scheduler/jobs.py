from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import date
from aiogram import Bot
from db import UserRepo, TaskRepo, PlanRepo
from ai.scheduler import generate_day_plan, generate_evening_summary

scheduler = AsyncIOScheduler()


def setup_scheduler(bot: Bot):
    scheduler.add_job(
        send_morning_plan,
        CronTrigger(hour=9, minute=0),
        args=[bot],
        id="morning_plan"
    )
    
    scheduler.add_job(
        send_evening_summary,
        CronTrigger(hour=21, minute=0),
        args=[bot],
        id="evening_summary"
    )
    
    scheduler.start()


async def send_morning_plan(bot: Bot):
    users = await get_all_users()
    today = date.today().isoformat()
    
    for user in users:
        tasks = await TaskRepo.get_user_tasks(user.id)
        if not tasks:
            continue
        
        plan = await PlanRepo.get(user.id, today)
        
        if not plan:
            plan_text = await generate_day_plan(tasks, user.timezone)
            await PlanRepo.create(user.id, today, plan_text)
        else:
            plan_text = plan.schedule
        
        try:
            await bot.send_message(
                user.id,
                f"🌅 <b>Доброе утро!</b>\n\n"
                f"📅 Вот твой план на сегодня:\n\n{plan_text}"
            )
        except Exception as e:
            print(f"Failed to send morning plan to {user.id}: {e}")


async def send_evening_summary(bot: Bot):
    users = await get_all_users()
    
    for user in users:
        tasks = await TaskRepo.get_user_tasks(user.id, include_completed=True)
        
        if not tasks:
            continue
        
        summary = await generate_evening_summary(tasks)
        
        try:
            await bot.send_message(user.id, summary)
        except Exception as e:
            print(f"Failed to send evening summary to {user.id}: {e}")


async def get_all_users():
    import aiosqlite
    from db.database import get_db
    from db.models import User
    
    async with await get_db() as db:
        async with db.execute("SELECT * FROM users") as cursor:
            rows = await cursor.fetchall()
            return [User(*row) for row in rows]
