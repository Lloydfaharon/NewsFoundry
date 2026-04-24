from dotenv import load_dotenv
load_dotenv()
from contextlib import asynccontextmanager
from .database import init_db
from fastapi import FastAPI, HTTPException, Depends # Ajout de HTTPException et Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel # Ajout pour le schéma de login
from sqlmodel import Session, select # Ajout pour la base de données
import uvicorn
import bcrypt # Ajout pour vérifier le mot de passe
from .auth import create_access_token, get_current_user # On importe la fonction du nouveau fichier auth.py
from .models import User, Chat # On importe le modèle User et Chat
from .database import engine # On importe l'engine pour la session
from .agent import newsfoundry_agent # Import de l'agent PydanticAI
from .news_service import get_today_news_context # Import du service d'API externe News
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, UserPromptPart, TextPart, SystemPromptPart
from pydantic import TypeAdapter
from .press_agent import press_agent # Import de l'agent spécialisé
import json

# --- SCHÉMA DE DONNÉES ---
class LoginRequest(BaseModel):
    email: str
    password: str

class MessageRequest(BaseModel):
    content: str

class PressReleaseRequest(BaseModel):
    topic: str

# 1. On définit le cycle de vie pour initialiser la DB au démarrage sur Railway
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db() # Création des tables
    yield

app = FastAPI(lifespan=lifespan)

# 2. On autorise le Frontend à appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], 
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def hello():
    return {"message": "👋 NewsFoundry API is online"}

# --- NOUVELLE ROUTE : LOGIN ---
@app.post("/login")
async def login(data: LoginRequest):
    with Session(engine) as session:
        # 1. Chercher l'utilisateur par email
        statement = select(User).where(User.email == data.email)
        user = session.exec(statement).first()

        # 2. Vérification de l'utilisateur et du mot de passe
        if not user:
            raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
        
        # Vérification du hash bcrypt
        password_match = bcrypt.checkpw(
            data.password.encode("utf-8"), 
            user.hashed_password.encode("utf-8")
        )

        if not password_match:
            raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

        # 3. Génération du Token JWT via notre fichier auth.py
        access_token = create_access_token(data={"sub": user.email})

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

# --- ROUTES CHAT (SÉCURISÉES) ---
@app.post("/chats")
async def create_chat(user: User = Depends(get_current_user)):
    # 1. On fetch les dernières news via World News API
    news_context = await get_today_news_context()
    
    # 2. On rédige le system prompt officiel de cette conversation incluant ces news spécifiques
    full_system_prompt = (
        "Tu es l'assistant de NewsFoundry, une application destinée à la gestion "
        "d'articles et de tâches journalistiques.\n"
        "Réponds systématiquement en utilisant le format Markdown.\n\n"
        "DIRECTIVES STRICTES :\n"
        "1. Ne montre JAMAIS tes appels techniques d'outils (ex: search_news_tool(...)) à l'utilisateur.\n"
        "2. Si tu lances un outil, attends d'avoir le résultat pour rédiger ta réponse humaine.\n"
        "3. Si tu ne trouves rien malgré tes recherches, explique-le poliment sans inventer de syntaxe technique.\n\n"
        f"{news_context}"
    )

    with Session(engine) as session:
        # 3. On enregistre en base : ce prompt est figé pour l'éternité dans CE chat !
        new_chat = Chat(user_id=user.id, system_prompt=full_system_prompt)
        session.add(new_chat)
        session.commit()
        session.refresh(new_chat)
        return {"id": new_chat.id}

@app.get("/chats")
async def list_chats(user: User = Depends(get_current_user)):
    with Session(engine) as session:
        statement = select(Chat).where(Chat.user_id == user.id)
        chats = session.exec(statement).all()
        return [{"id": c.id} for c in chats]

@app.get("/chats/{chat_id}")
async def get_chat_history(chat_id: int, user: User = Depends(get_current_user)):
    with Session(engine) as session:
        chat = session.get(Chat, chat_id)
        if not chat or chat.user_id != user.id:
            raise HTTPException(status_code=403, detail="Accès non autorisé à cette discussion")
        
        # On simplifie l'historique technique pour le Frontend (Affichage)
        simplified_history = []
        try:
            # On purge et convertit l'historique brut de la base en objets ModelMessage
            ta = TypeAdapter(list[ModelMessage])
            messages = ta.validate_python(chat.history)
            
            for msg in messages:
                # On ne garde que les messages qui ont du contenu textuel lisible
                if isinstance(msg, ModelRequest):
                    for part in msg.parts:
                        if isinstance(part, UserPromptPart):
                            simplified_history.append({"role": "user", "content": part.content})
                elif isinstance(msg, ModelResponse):
                    for part in msg.parts:
                        if isinstance(part, TextPart):
                            simplified_history.append({"role": "model", "content": part.content})
            
            # Fallback : si la liste simplifiée est vide mais que l'historique contient des vieux messages textuels
            if not simplified_history and chat.history and isinstance(chat.history[0], dict) and "role" in chat.history[0]:
                return chat.history
                
        except Exception as e:
            print(f"Erreur simplification historique: {e}")
            return chat.history # Retourne le brut en cas de doute
            
        return {
            "messages": simplified_history,
            "press_releases": chat.press_releases or []
        }

@app.post("/chats/{chat_id}/messages")
async def send_message(chat_id: int, message: MessageRequest, user: User = Depends(get_current_user)):
    with Session(engine) as session:
        chat = session.get(Chat, chat_id)
        if not chat or chat.user_id != user.id:
            raise HTTPException(status_code=403, detail="Accès non autorisé à cette discussion")
        
        # 1. Chargement et Désérialisation robuste de l'historique
        ta = TypeAdapter(list[ModelMessage])
        try:
            raw_history = ta.validate_python(chat.history)
            
            # NETTOYAGE : On retire les SystemPromptPart de l'historique chargé.
            # Pourquoi ? Parce que newsfoundry_agent.run() va ré-injecter le prompt système 
            # via le décorateur @system_prompt (utilisant l'argument 'deps').
            # Si on laisse l'ancien, Mistral reçoit deux prompts systèmes, ce qui casse l'ordre.
            pydantic_ai_history = []
            for msg in raw_history:
                if isinstance(msg, ModelRequest):
                    # On filtre les parties qui ne sont pas des SystemPromptPart
                    filtered_parts = [p for p in msg.parts if not isinstance(p, SystemPromptPart)]
                    if filtered_parts:
                        pydantic_ai_history.append(ModelRequest(parts=filtered_parts, kind=msg.kind, timestamp=msg.timestamp))
                else:
                    pydantic_ai_history.append(msg)
                    
        except Exception as e:
            print(f"Historique incompatible ou vide ({e}), on repart à zéro.")
            pydantic_ai_history = []
                
        # 2. Exécution de l'Agent PydanticAI
        try:
            result = await newsfoundry_agent.run(
                message.content, 
                deps=chat.system_prompt,
                message_history=pydantic_ai_history
            )
            
            # On récupère la réponse textuelle finale (en ignorant les parties techniques types ToolCall)
            # On cherche spécifiquement la dernière partie textuelle de la réponse
            response_content = ""
            for msg in result.new_messages():
                if isinstance(msg, ModelResponse):
                    for part in msg.parts:
                        if isinstance(part, TextPart):
                            response_content += part.content
            
            # Fallback si aucune nouvelle partie textuelle n'est trouvée
            if not response_content:
                response_content = str(getattr(result, "output", getattr(result, "data", "")))
            
            # Nettoyage final pour supprimer d'éventuelles hallucinations résiduelles
            if "search_news_tool" in response_content:
                 response_content = "Je n'ai pas pu obtenir de résultats précis pour cette recherche. Pourriez-vous reformuler ?"
            
            # 3. Sérialisation de l'historique COMPLET pour la prochaine fois
            updated_messages = result.all_messages()
            chat.history = ta.dump_python(updated_messages, mode='json')
            
            # 4. Sauvegarde
            session.add(chat)
            session.commit()
            
            return {"response": response_content}

        except Exception as e:
            import traceback
            print(f"--- ERREUR CRITIQUE AGENT ---")
            traceback.print_exc()
            # On renvoie une erreur plus parlante pour le debug
            raise HTTPException(
                status_code=500, 
                detail=f"Erreur lors de la génération de la réponse : {str(e)}"
            )

# --- NOUVELLE ROUTE : GÉNÉRATION DE REVUE DE PRESSE ---
@app.post("/chats/{chat_id}/press-release")
async def generate_press_release(chat_id: int, request: PressReleaseRequest, user: User = Depends(get_current_user)):
    with Session(engine) as session:
        # 1. Vérification de la propriété du chat
        chat = session.get(Chat, chat_id)
        if not chat or chat.user_id != user.id:
            raise HTTPException(status_code=403, detail="Accès non autorisé")

        # 2. Re-préparation de l'historique technique (pour que l'IA ait tout le contexte)
        ta = TypeAdapter(list[ModelMessage])
        try:
            # On utilise tout l'historique technique, sans filtre, pour un maximum de contexte nutritif pour l'IA
            pydantic_ai_history = ta.validate_python(chat.history)
        except Exception as e:
            print(f"Erreur historique : {e}")
            pydantic_ai_history = []

        # 3. Appel de l'agent spécialisé
        try:
            result = await press_agent.run(
                f"Sujet de la revue de presse : {request.topic}",
                message_history=pydantic_ai_history
            )
            
            # result.output contient déjà un objet de type PressRelease (grâce à output_type)
            new_release = result.output.model_dump()
            
            # 4. Enregistrement en base de données
            # On réaffecte la liste pour forcer SQLAlchemy à détecter le changement
            current_releases = list(chat.press_releases)
            current_releases.append(new_release)
            chat.press_releases = current_releases
            
            session.add(chat)
            session.commit()
            
            return new_release

        except Exception as e:
            print(f"Erreur génération revue : {e}")
            raise HTTPException(status_code=500, detail="Échec de la génération de la revue de presse")

# --- NOUVELLE ROUTE : RÉCUPÉRATION GLOBALE DES REVUES ---
@app.get("/press-releases")
async def list_all_press_releases(user: User = Depends(get_current_user)):
    with Session(engine) as session:
        statement = select(Chat).where(Chat.user_id == user.id)
        chats = session.exec(statement).all()
        all_releases = []
        for chat in chats:
            if chat.press_releases:
                for release in chat.press_releases:
                    release_copy = dict(release)
                    release_copy["chat_id"] = chat.id
                    all_releases.append(release_copy)
        return all_releases


if __name__ == "__main__":
    # Note : en local on utilise "main:app" pour que le reload fonctionne
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)