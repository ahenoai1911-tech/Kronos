import aiosqlite
from datetime import datetime, date
from typing import List, Optional
from .database import get_db
from .models import User, Task, Plan, Stats


class UserRepo:
    @staticmethod
    async def create(user_id: int, username: str = None) -> User:
        async with await get_db() as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)",
                (user_id, username)
            )
            await db.commit()
            return await UserRepo.get(user_id)
    
    @staticmethod
    async def get(user_id: int) -> Optional[User]:
        async with await get_db() as db:
            async with db.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return User(*row)
        return None
    
    @staticmethod
    async def update_settings(user_id: int, timezone: str = None, 
                              morning_time: str = None, evening_time: str = None):
        async with await get_db() as db:
            updates = []
            values = []
            if timezone:
                updates.append("timezone = ?")
                values.append(timezone)
            if morning_time:
                updates.append("morning_time = ?")
                values.append(morning_time)
            if evening_time:
                updates.append("evening_time = ?")
                values.append(evening_time)
            values.append(user_id)
            await db.execute(
                f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
                values
            )
            await db.commit()


class TaskRepo:
    @staticmethod
    async def create(user_id: int, title: str, description: str = None,
                     category: str = "general", priority: int = 2,
                     deadline: str = None, estimated_minutes: int = None) -> Task:
        async with await get_db() as db:
            cursor = await db.execute(
                """INSERT INTO tasks 
                   (user_id, title, description, category, priority, deadline, estimated_minutes)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (user_id, title, description, category, priority, deadline, estimated_minutes)
            )
            await db.commit()
            return await TaskRepo.get(cursor.lastrowid)
    
    @staticmethod
    async def get(task_id: int) -> Optional[Task]:
        async with await get_db() as db:
            async with db.execute(
                "SELECT * FROM tasks WHERE id = ?", (task_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Task(*row)
        return None
    
    @staticmethod
    async def get_user_tasks(user_id: int, status: str = None, 
                             include_completed: bool = False) -> List[Task]:
        async with await get_db() as db:
            query = "SELECT * FROM tasks WHERE user_id = ?"
            params = [user_id]
            
            if status:
                query += " AND status = ?"
                params.append(status)
            elif not include_completed:
                query += " AND status != 'completed'"
            
            query += " ORDER BY priority DESC, deadline ASC"
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [Task(*row) for row in rows]
    
    @staticmethod
    async def update(task_id: int, **kwargs) -> Optional[Task]:
        async with await get_db() as db:
            updates = [f"{k} = ?" for k in kwargs.keys()]
            values = list(kwargs.values())
            values.append(task_id)
            await db.execute(
                f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?",
                values
            )
            await db.commit()
            return await TaskRepo.get(task_id)
    
    @staticmethod
    async def complete(task_id: int) -> Optional[Task]:
        async with await get_db() as db:
            now = datetime.now().isoformat()
            await db.execute(
                "UPDATE tasks SET status = 'completed', completed_at = ? WHERE id = ?",
                (now, task_id)
            )
            await db.commit()
            return await TaskRepo.get(task_id)
    
    @staticmethod
    async def delete(task_id: int):
        async with await get_db() as db:
            await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            await db.commit()


class PlanRepo:
    @staticmethod
    async def create(user_id: int, date_str: str, schedule: str) -> Plan:
        async with await get_db() as db:
            cursor = await db.execute(
                "INSERT OR REPLACE INTO plans (user_id, date, schedule) VALUES (?, ?, ?)",
                (user_id, date_str, schedule)
            )
            await db.commit()
            return await PlanRepo.get(user_id, date_str)
    
    @staticmethod
    async def get(user_id: int, date_str: str) -> Optional[Plan]:
        async with await get_db() as db:
            async with db.execute(
                "SELECT * FROM plans WHERE user_id = ? AND date = ?",
                (user_id, date_str)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Plan(*row)
        return None


class StatsRepo:
    @staticmethod
    async def create_or_update(user_id: int, date_str: str, 
                               tasks_completed: int = None, tasks_total: int = None,
                               focus_score: float = None, notes: str = None) -> Stats:
        async with await get_db() as db:
            existing = await StatsRepo.get(user_id, date_str)
            if existing:
                updates = []
                values = []
                if tasks_completed is not None:
                    updates.append("tasks_completed = ?")
                    values.append(tasks_completed)
                if tasks_total is not None:
                    updates.append("tasks_total = ?")
                    values.append(tasks_total)
                if focus_score is not None:
                    updates.append("focus_score = ?")
                    values.append(focus_score)
                if notes is not None:
                    updates.append("notes = ?")
                    values.append(notes)
                values.extend([user_id, date_str])
                await db.execute(
                    f"UPDATE stats SET {', '.join(updates)} WHERE user_id = ? AND date = ?",
                    values
                )
            else:
                await db.execute(
                    """INSERT INTO stats 
                       (user_id, date, tasks_completed, tasks_total, focus_score, notes)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (user_id, date_str, tasks_completed or 0, tasks_total or 0, 
                     focus_score, notes)
                )
            await db.commit()
            return await StatsRepo.get(user_id, date_str)
    
    @staticmethod
    async def get(user_id: int, date_str: str) -> Optional[Stats]:
        async with await get_db() as db:
            async with db.execute(
                "SELECT * FROM stats WHERE user_id = ? AND date = ?",
                (user_id, date_str)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Stats(*row)
        return None
