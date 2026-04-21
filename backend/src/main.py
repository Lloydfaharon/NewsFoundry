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
from pydantic_ai.messages import ModelRequest, ModelResponse, UserPromptPart, TextPart

# --- SCHÉMA DE DONNÉES ---
class LoginRequest(BaseModel):
    email: str
    password: str

class MessageRequest(BaseModel):
    content: str

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
        return chat.history

@app.post("/chats/{chat_id}/messages")
async def send_message(chat_id: int, message: MessageRequest, user: User = Depends(get_current_user)):
    with Session(engine) as session:
        chat = session.get(Chat, chat_id)
        if not chat or chat.user_id != user.id:
            raise HTTPException(status_code=403, detail="Accès non autorisé à cette discussion")
        
        # 1. Préparation de l'historique PydanticAI (ModelMessage objects)
        pydantic_ai_history = []
        for msg in chat.history:
            if msg.get("role") == "user":
                pydantic_ai_history.append(ModelRequest(parts=[UserPromptPart(content=msg.get("content", ""))]))
            else:
                pydantic_ai_history.append(ModelResponse(parts=[TextPart(content=msg.get("content", ""))]))
                
        # 2. Exécution de l'Agent PydanticAI
        # On injecte l'historique converti ET notre system_prompt dynamique sauvegardé en BDD via 'deps'
        try:
            response = await newsfoundry_agent.run(
                message.content, 
                deps=chat.system_prompt,
                message_history=pydantic_ai_history
            )
            response_content = str(getattr(response, "data", getattr(response, "output", "")))
        except Exception as e:
            print(f"Erreur run: {e}")
            response_content = "Désolé, une erreur technique m'a empêché de répondre."
        
        # 3. Mise à jour de l'historique JSON stocké en BDD (Copie)
        history = list(chat.history) 
        history.append({"role": "user", "content": message.content})
        history.append({"role": "model", "content": response_content})
        
        # 4. Sauvegarde
        chat.history = history
        session.add(chat)
        session.commit()
        
        return {"response": response_content}

if __name__ == "__main__":
    # Note : en local on utilise "main:app" pour que le reload fonctionne
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)