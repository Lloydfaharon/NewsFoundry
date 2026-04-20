from pydantic_ai import Agent

# Modèle de base pour l'agent (PydanticAI détecte la clé MISTRAL_API_KEY)
model_name = "mistral:mistral-large-latest"

# On configure l'agent avec un prompt système fort pour lui donner une identité
newsfoundry_agent = Agent(
    model_name,
    system_prompt=(
        "Tu es l'assistant de NewsFoundry, une application destinée à la gestion "
        "d'articles et de tâches journalistiques.\n"
        "Ton objectif est d'aider l'utilisateur (un rédacteur ou journaliste) de manière "
        "précise et courtoise.\n"
        "Réponds systématiquement en utilisant le format Markdown "
        "(avec gras, listes, etc.) pour rendre tes textes plus lisibles."
    )
)
