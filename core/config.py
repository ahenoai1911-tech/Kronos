from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    BOT_TOKEN: str
    OPENAI_API_KEY: str = ""
    WEBAPP_URL: str = ""
    ADMIN_IDS: List[int] = []
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
