from contextlib import asynccontextmanager
from .database import init_db  # Ton correctif avec le point
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 1. On définit le cycle de vie pour initialiser la DB au démarrage sur Railway
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db() # Création des tables
    yield

app = FastAPI(lifespan=lifespan)

# 2. On autorise le Frontend à appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def hello():
    return {"message": "👋 NewsFoundry API is online"}

if __name__ == "__main__":
    # Note : en local on utilise "main:app" pour que le reload fonctionne
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)