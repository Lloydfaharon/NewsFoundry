from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
from sqlmodel import Session
from news_service import search_detailed_news_with_urls
from models import Chat
from database import engine

@dataclass
class AgentDeps:
    system_prompt: str
    chat_id: int

# Modèle de base pour l'agent
model_name = "mistral:mistral-large-latest"

# On configure l'agent pour accepter nos dépendances structurées
newsfoundry_agent = Agent(
    model_name,
    deps_type=AgentDeps
)

@newsfoundry_agent.system_prompt
def dynamic_prompt(ctx: RunContext[AgentDeps]) -> str:
    """Récupère le prompt système depuis nos dépendances."""
    return ctx.deps.system_prompt

@newsfoundry_agent.tool
async def search_news_tool(ctx: RunContext[AgentDeps], query: str) -> str:
    """
    Recherche des articles de presse et mémorise leurs liens pour la revue de presse.
    
    Args:
        query: Le sujet de recherche court et précis.
    """
    # 1. On effectue la recherche
    search_results_text, urls = await search_detailed_news_with_urls(query)
    
    # 2. On sauvegarde les URLs dans la base de données pour le futur RAG
    if urls:
        with Session(engine) as session:
            chat = session.get(Chat, ctx.deps.chat_id)
            if chat:
                # On fusionne avec les URLs déjà présentes sans faire de doublons
                existing_urls = set(chat.loaded_articles or [])
                existing_urls.update(urls)
                chat.loaded_articles = list(existing_urls)
                
                session.add(chat)
                session.commit()
                print(f"✅ {len(urls)} URLs mémorisées pour le chat {ctx.deps.chat_id}")
            
    return search_results_text
