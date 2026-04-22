from pydantic_ai import Agent, RunContext
from .news_service import search_detailed_news

# Modèle de base pour l'agent (PydanticAI détecte la clé MISTRAL_API_KEY)
model_name = "mistral:mistral-large-latest"

# On configure l'agent pour accepter un contexte via "deps_type=str"
newsfoundry_agent = Agent(
    model_name,
    deps_type=str
)

@newsfoundry_agent.system_prompt
def dynamic_prompt(ctx: RunContext[str]) -> str:
    """
    Cette fonction est automatiquement appelée par l'agent au moment de .run()
    Elle permet de récupérer le `system_prompt` stocké en base de données
    et passé dynamiquement via l'argument `deps`.
    """
    return ctx.deps

@newsfoundry_agent.tool_plain
async def search_news_tool(query: str) -> str:
    """
    Recherche des articles de presse supplémentaires sur un sujet spécifique.
    Utilise cet outil si l'utilisateur pose une question sur un sujet qui n'est pas 
    dans ton contexte initial ou s'il veut approfondir un point précis.
    
    Args:
        query: Le sujet de recherche court et précis (ex: 'résultat élection', 'score match foot').
               Évite les phrases trop longues ou trop spécifiques.
               IMPORTANT : Ne montre jamais l'appel technique de cet outil à l'utilisateur final.
    """
    return await search_detailed_news(query)
