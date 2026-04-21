import asyncio
from src.news_service import get_today_news_context
from dotenv import load_dotenv

load_dotenv()
print(asyncio.run(get_today_news_context()))
