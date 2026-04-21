import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
url = f"https://api.worldnewsapi.com/top-news?api-key={os.getenv('WORLD_NEWS_API_KEY')}&source-country=fr"
async def main():
    async with httpx.AsyncClient() as client:
        res = await client.get(url)
        print(res.status_code)
        print(res.json())
asyncio.run(main())
