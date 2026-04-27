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
            
            context = "Voici les actualités récentes pour t'aider dans tes réponses :\n\n"
            urls = []
            
            # On ne prend que les 5 premiers articles
            for cluster in data.get("top_news", [])[:5]:
                for article in cluster.get("news", [])[:1]:
                    title = article.get("title", "Titre inconnu")
                    text = article.get("text", "")
                    link = article.get("url", "")
                    if link:
                        urls.append(link)
                        
                    summary = text[:200] + "..." if len(text) > 200 else text
                    context += f"- **{title}** : {summary}\n"
                    
            return context, urls

    except Exception as e:
        print(f"Exception lors du fetch des news : {str(e)}")
        return "Tu es l'assistant NewsFoundry. (Erreur de connexion au service d'actualités)", []

async def search_detailed_news(query: str) -> str:
    """
    Recherche des articles sur le web via l'API World News.
    Sera utilisé par le Tool de l'Agent.
    """
    WORLD_NEWS_API_KEY = os.getenv("WORLD_NEWS_API_KEY")
    if not WORLD_NEWS_API_KEY:
         return "Recherche impossible : Clé d'API World News manquante."
         
    url = f"https://api.worldnewsapi.com/search-news?api-key={WORLD_NEWS_API_KEY}&text={query}&language=fr&number=3"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            
            if response.status_code != 200:
                print(f"Erreur API Search News: {response.status_code} - {response.text}")
                return "Désolé, le service de recherche est temporairement indisponible."
            
            data = response.json()
            articles = data.get("news", [])
            
            if not articles:
                return (
                    f"Je n'ai trouvé aucun article récent pour la recherche : '{query}'. "
                    "Suggère à l'utilisateur de reformuler sa demande avec des mots-clés plus larges "
                    "ou propose-lui de passer à un autre sujet."
                )
                 
            # Purification des résultats pour ne pas surcharger le modèle
            result_string = f"Voici les articles trouvés pour '{query}' :\n\n"
            for article in articles:
                title = article.get("title", "Titre inconnu")
                text = article.get("text", "")
                url = article.get("url", "Pas de lien")
                
                # Résumé limité à 300 caractères
                summary = text[:300] + "..." if len(text) > 300 else text
                
                result_string += f"- **{title}**\n  *Résumé* : {summary}\n  *Lien* : {url}\n\n"
                
            return result_string

    except Exception as e:
        print(f"Exception lors de la recherche spécifique : {str(e)}")
        return f"Erreur technique lors de la recherche sur le sujet : {query}"

async def search_detailed_news_with_urls(query: str) -> tuple[str, list[str]]:
    """
    Similaire à search_detailed_news, mais renvoie un tuple (texte_pur, liste_urls).
    """
    WORLD_NEWS_API_KEY = os.getenv("WORLD_NEWS_API_KEY")
    if not WORLD_NEWS_API_KEY:
         return "Recherche impossible : Clé d'API World News manquante.", []
         
    url = f"https://api.worldnewsapi.com/search-news?api-key={WORLD_NEWS_API_KEY}&text={query}&language=fr&number=3"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            if response.status_code != 200:
                return "Désolé, le service de recherche est temporairement indisponible.", []
            
            data = response.json()
            articles = data.get("news", [])
            if not articles:
                return f"Aucun article trouvé pour '{query}'.", []
            
            result_string = f"Voici les articles trouvés pour '{query}' :\n\n"
            urls = []
            for article in articles:
                title = article.get("title", "Titre inconnu")
                text = article.get("text", "")
                link = article.get("url", "")
                if link:
                    urls.append(link)
                
                summary = text[:300] + "..." if len(text) > 300 else text
                result_string += f"- **{title}**\n  *Résumé* : {summary}\n  *Lien* : {link}\n\n"
                
            return result_string, urls

    except Exception as e:
        print(f"Exception recherche avec URLs : {str(e)}")
        return f"Erreur technique lors de la recherche sur le sujet : {query}", []
