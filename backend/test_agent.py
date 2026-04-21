import asyncio
from src.main import newsfoundry_agent

async def main():
    try:
        response = await newsfoundry_agent.run("Comment ça va ?", deps="Test system prompt")
        print(dir(response))
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(main())
