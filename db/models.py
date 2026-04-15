from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    id: int
    username: Optional[str]
    timezone: str = "UTC"
    morning_time: str = "09:00"
    evening_time: str = "21:00"
    created_at: Optional[datetime] = None


@dataclass
class Task:
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    category: str = "general"
    priority: int = 2
    deadline: Optional[str] = None
    estimated_minutes: Optional[int] = None
    status: str = "pending"
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class Plan:
    id: int
    user_id: int
    date: str
    schedule: str
    created_at: Optional[datetime] = None


@dataclass
class Stats:
    id: int
    user_id: int
    date: str
    tasks_completed: int = 0
    tasks_total: int = 0
    focus_score: Optional[float] = None
    notes: Optional[str] = None
