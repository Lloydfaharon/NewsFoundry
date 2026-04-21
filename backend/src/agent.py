from pydantic_ai import Agent, RunContext

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
