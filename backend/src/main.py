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
    allow_origin_regex="https://.*\.vercel\.app",
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
    with Session(engine) as session:
        new_chat = Chat(user_id=user.id)
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
        
        # 1. Ajouter le message de l'utilisateur à l'historique
        # Attention: history étant JSON, il faut cloner la liste pour que SQLAlchemy détecte le changement
        history = list(chat.history) 
        history.append({"role": "user", "content": message.content})
        
        # 2. Exécuter l'Agent PydanticAI avec l'historique complet
        # Les modèles pydantic-ai préfèrent une liste explicite ou gèrent seuls l'historique 
        # Mais dans le cas de base string.
        # Pour utiliser correctement l'historique avec PydanticAI :
        prompt = message.content
        # On pourrait passer history complet, mais pour un chat simple :
        response = await newsfoundry_agent.run(prompt)
        
        # 3. Ajouter la réponse du LLM
        response_content = getattr(response, "data", getattr(response, "output", "No response content extracted"))
        if type(response_content) is not str:
            response_content = str(response_content)
        history.append({"role": "model", "content": response_content})
        
        # 4. Sauvegarder dans la DB
        chat.history = history
        session.add(chat)
        session.commit()
        
        return {"response": response_content}

if __name__ == "__main__":
    # Note : en local on utilise "main:app" pour que le reload fonctionne
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)