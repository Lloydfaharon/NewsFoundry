import httpx
import os
from typing import Optional

async def get_today_news_context() -> str:
    # On récupère la clé, sans elle l'appel est impossible
    WORLD_NEWS_API_KEY = os.getenv("WORLD_NEWS_API_KEY")
    if not WORLD_NEWS_API_KEY:
        print("ATTENTION: WORLD_NEWS_API_KEY est introuvable. On renvoie un contexte vide.")
        return "Tu es l'assistant NewsFoundry. (Mode Hors-Ligne: API News introuvable)"

    url = f"https://api.worldnewsapi.com/top-news?api-key={WORLD_NEWS_API_KEY}&source-country=fr&language=fr"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            
            if response.status_code != 200:
                print(f"Erreur API World News: {response.status_code}")
                return "Tu es l'assistant NewsFoundry. (Service d'actualités temporairement indisponible)"
            
            data = response.json()
            context = "Voici les actualités récentes pour t'aider dans tes réponses :\n\n"
            
            # On ne prend que les 5 premiers articles pour ne pas saturer le LLM (fenêtre de contexte)
            for cluster in data.get("top_news", [])[:5]:
                for article in cluster.get("news", [])[:1]:
                    title = article.get("title", "Titre inconnu")
                    text = article.get("text", "")
                    summary = text[:200] + "..." if len(text) > 200 else text
                    context += f"- **{title}** : {summary}\n"
                    
            return context

    except Exception as e:
        print(f"Exception lors du fetch des news : {str(e)}")
        return "Tu es l'assistant NewsFoundry. (Erreur de connexion au service d'actualités)"
