from pydantic_ai import Agent
from .schemas import PressRelease

# On définit l'agent avec result_type. 
# C'est ce paramètre qui "force" l'IA à renvoyer un objet JSON valide 
# correspondant exactement à notre classe PressRelease.
press_agent = Agent(
    'mistral:mistral-large-latest',
    output_type=PressRelease, 
    system_prompt=(
        "Tu es un rédacteur en chef expert en synthèse de documents. "
        "Ton rôle est d'analyser l'historique d'une discussion entre un utilisateur et un assistant "
        "pour en extraire les points clés et rédiger une revue de presse structurée sur un sujet précis. "
        "Consignes :\n"
        "1. Utilise exclusivement les informations présentes dans l'historique de la discussion.\n"
        "2. Rédige un titre percutant.\n"
        "3. Fais une synthèse générale de la discussion sur le sujet.\n"
        "4. Répertorie chaque article ou déclaration mentionné avec un titre court et un résumé fidèle."
    )
)
