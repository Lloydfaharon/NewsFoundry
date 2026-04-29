from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str = Field()
    
    # Relation : Un utilisateur peut avoir plusieurs chats
    chats: List["Chat"] = Relationship(back_populates="user")

class Chat(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Historique de la conversation, stocké sous forme de JSON
    history: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSON))
    
    # Antisèche : le prompt généré avec les news
    system_prompt: str = Field(default="Tu es l'assistant NewsFoundry.")
    
    # Clé étrangère vers l'utilisateur
    user_id: int = Field(foreign_key="user.id")
    
    # Relation : Un chat a un seul utilisateur
    user: User = Relationship(back_populates="chats")

    # Nouveau : Liste des revues de presse générées pour ce chat
    press_releases: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSON))

    # RAG : On stocke les URLs des articles chargés via les outils pour LlamaIndex
    loaded_articles: List[str] = Field(default=[], sa_column=Column(JSON))
    
    # Date de création
    created_at: datetime = Field(default_factory=datetime.utcnow)