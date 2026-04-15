import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from core.config import settings


async def parse_task_text(text: str) -> Dict[str, Any]:
    if not settings.OPENAI_API_KEY:
        return _parse_local(text)
    
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""Ты помощник для парсинга задач. Извлеки из текста:
- title: название задачи (кратко)
- description: описание (если есть детали)
- deadline: дата дедлайна в формате YYYY-MM-DD (если указана, сегодня: {today})
- priority: 1-3 (1=высокий, 2=средний, 3=низкий)
- category: work/home/study/sport/other
- estimated_minutes: примерное время в минутах (если указано)

Ответь ТОЛЬКО JSON без markdown."""
                },
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        result = response.choices[0].message.content
        return json.loads(result)
    
    except Exception as e:
        print(f"OpenAI error: {e}")
        return _parse_local(text)


def _parse_local(text: str) -> Dict[str, Any]:
    result = {
        "title": text[:100],
        "priority": 2,
        "category": "general"
    }
    
    text_lower = text.lower()
    
    if any(w in text_lower for w in ["срочно", "важно", "немедленно", "urgent", "important"]):
        result["priority"] = 1
    elif any(w in text_lower for w in ["позже", "когда-нибудь", "later", "someday"]):
        result["priority"] = 3
    
    if any(w in text_lower for w in ["работ", "meet", "клиент", "проект", "work"]):
        result["category"] = "work"
    elif any(w in text_lower for w in ["дом", "квартир", "home", "уборк"]):
        result["category"] = "home"
    elif any(w in text_lower for w in ["учеб", "курс", "learn", "study", "экзамен"]):
        result["category"] = "study"
    elif any(w in text_lower for w in ["спорт", "тренаж", "gym", "fitness", "бег"]):
        result["category"] = "sport"
    
    if "завтра" in text_lower:
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        result["deadline"] = tomorrow
    elif "сегодня" in text_lower or "вечер" in text_lower or "утро" in text_lower:
        result["deadline"] = datetime.now().strftime("%Y-%m-%d")
    
    import re
    time_match = re.search(r"(\d{1,2}):(\d{2})", text)
    if time_match:
        pass
    
    return result
