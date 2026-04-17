from contextlib import asynccontextmanager
from .database import init_db
from fastapi import FastAPI, HTTPException # Ajout de HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel # Ajout pour le schéma de login
from sqlmodel import Session, select # Ajout pour la base de données
import uvicorn
import bcrypt # Ajout pour vérifier le mot de passe
from .auth import create_access_token # On importe la fonction du nouveau fichier auth.py
from .models import User # On importe le modèle User
from .database import engine # On importe l'engine pour la session

# --- SCHÉMA DE DONNÉES ---
class LoginRequest(BaseModel):
    email: str
    password: str

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

if __name__ == "__main__":
    # Note : en local on utilise "main:app" pour que le reload fonctionne
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)