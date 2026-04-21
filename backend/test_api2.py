import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
url = f"https://api.worldnewsapi.com/top-news?source-country=fr&language=fr&api-key={os.getenv('WORLD_NEWS_API_KEY')}"
async def main():
    async with httpx.AsyncClient() as client:
        res = await client.get(url)
        print(res.status_code, res.text)
asyncio.run(main())
