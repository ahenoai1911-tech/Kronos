import aiosqlite
from typing import Optional
import os

DB_PATH = "kronos.db"


async def init_db():
    os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else ".", exist_ok=True)
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                timezone TEXT DEFAULT 'UTC',
                morning_time TEXT DEFAULT '09:00',
                evening_time TEXT DEFAULT '21:00',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT DEFAULT 'general',
                priority INTEGER DEFAULT 2,
                deadline TEXT,
                estimated_minutes INTEGER,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                schedule TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                tasks_completed INTEGER DEFAULT 0,
                tasks_total INTEGER DEFAULT 0,
                focus_score REAL,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)
        await db.commit()


async def get_db():
    return await aiosqlite.connect(DB_PATH)
