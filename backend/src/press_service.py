from llama_index.core import SummaryIndex, Document
from llama_index.readers.web import SimpleWebPageReader
from schemas import PressRelease

async def generate_rag_press_release(urls: list[str], topic: str) -> PressRelease:
    """
    Utilise LlamaIndex pour lire le contenu complet des URLs et générer une revue de presse.
    """
    print(f"🕵️ Analyse RAG lancée sur {len(urls)} articles pour le sujet : {topic}")
    
    # 1. Chargement du contenu complet des pages web (Scraping automatique)
    # html_to_text=True permet de nettoyer le code HTML pour ne garder que le texte.
    reader = SimpleWebPageReader(html_to_text=True)
    documents = reader.load_data(urls)
    
    # 2. Création d'un index rapide en mémoire
    # SummaryIndex est parfait ici car on veut une synthèse globale de tous les documents.
    index = SummaryIndex.from_documents(documents)
    
    # 3. Création du moteur de requête avec formatage Pydantic automatique
    # LlamaIndex va s'assurer que la réponse respecte exactement notre schéma PressRelease.
    query_engine = index.as_query_engine(response_format=PressRelease)
    
    # 4. On demande à l'IA de rédiger la revue en utilisant le contenu indexé
    prompt = (
        f"Rédige une revue de presse structurée et professionnelle sur le sujet : {topic}. "
        "Utilise EXCLUSIVEMENT les informations trouvées dans les articles fournis. "
        "Pour chaque article pertinent, rédige un résumé détaillé et captivant."
    )
    
    response = query_engine.query(prompt)
    
    # On retourne directement l'objet Pydantic contenu dans la réponse
    return response.response