from typing import Optional, List, Dict, Any
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
    
    # Clé étrangère vers l'utilisateur
    user_id: int = Field(foreign_key="user.id")
    
    # Relation : Un chat a un seul utilisateur
    user: User = Relationship(back_populates="chats")
