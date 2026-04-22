import asyncio
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelMessage

agent = Agent('mistral:mistral-large-latest')

@agent.system_prompt
def get_system_prompt(ctx: RunContext[str]) -> str:
    return ctx.deps

async def main():
    res = await agent.run("Hello", deps="SYSTEM CONTEXT")
    print("Messages after run 1:", [m.kind for m in res.all_messages()])
    
    # Run 2 with history
    res2 = await agent.run("How are you?", deps="SYSTEM CONTEXT", message_history=res.all_messages())
    print("Messages after run 2:", [m.kind for m in res2.all_messages()])

if __name__ == "__main__":
    asyncio.run(main())
