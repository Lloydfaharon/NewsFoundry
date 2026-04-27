from dotenv import load_dotenv
load_dotenv()
from contextlib import asynccontextmanager
from database import init_db # Import absolu
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Session, select
import uvicorn
import bcrypt
from auth import create_access_token, get_current_user # Import absolu
from models import User, Chat # Import absolu
from database import engine # Import absolu
from agent import newsfoundry_agent, AgentDeps # Import absolu
from press_service import generate_rag_press_release # Import absolu
from news_service import get_today_news_context # Import absolu
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, UserPromptPart, TextPart, SystemPromptPart
from pydantic import TypeAdapter
from press_agent import press_agent # Import absolu
import json

# --- SCHÉMA DE DONNÉES ---
class LoginRequest(BaseModel):
    email: str
    password: str

class MessageRequest(BaseModel):
    content: str

class PressReleaseRequest(BaseModel):
    topic: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

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

@app.post("/login")
async def login(data: LoginRequest):
    with Session(engine) as session:
        statement = select(User).where(User.email == data.email)
        user = session.exec(statement).first()
        if not user:
            raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
        password_match = bcrypt.checkpw(data.password.encode("utf-8"), user.hashed_password.encode("utf-8"))
        if not password_match:
            raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
        access_token = create_access_token(data={"sub": user.email})
        return {"access_token": access_token, "token_type": "bearer"}

@app.post("/chats")
async def create_chat(user: User = Depends(get_current_user)):
    news_context, initial_urls = await get_today_news_context()
    full_system_prompt = (
        "Tu es l'assistant de NewsFoundry, une application destinée à la gestion d'articles.\n"
        "Réponds systématiquement en utilisant le format Markdown.\n\n"
        f"{news_context}"
    )
    with Session(engine) as session:
        new_chat = Chat(user_id=user.id, system_prompt=full_system_prompt, loaded_articles=initial_urls)
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
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        simplified_history = []
        try:
            ta = TypeAdapter(list[ModelMessage])
            messages = ta.validate_python(chat.history)
            for msg in messages:
                if isinstance(msg, ModelRequest):
                    for part in msg.parts:
                        if isinstance(part, UserPromptPart):
                            simplified_history.append({"role": "user", "content": part.content})
                elif isinstance(msg, ModelResponse):
                    for part in msg.parts:
                        if isinstance(part, TextPart):
                            simplified_history.append({"role": "model", "content": part.content})
        except Exception as e:
            print(f"Erreur lors de la simplification de l'historique : {e}")
            return {"messages": [], "press_releases": chat.press_releases or []}
        
        return {"messages": simplified_history, "press_releases": chat.press_releases or []}

@app.post("/chats/{chat_id}/messages")
async def send_message(chat_id: int, message: MessageRequest, user: User = Depends(get_current_user)):
    with Session(engine) as session:
        chat = session.get(Chat, chat_id)
        if not chat or chat.user_id != user.id:
            raise HTTPException(status_code=403)
        ta = TypeAdapter(list[ModelMessage])
        try:
            raw_history = ta.validate_python(chat.history)
            pydantic_ai_history = []
            for msg in raw_history:
                if isinstance(msg, ModelRequest):
                    filtered_parts = [p for p in msg.parts if not isinstance(p, SystemPromptPart)]
                    if filtered_parts:
                        pydantic_ai_history.append(ModelRequest(parts=filtered_parts, kind=msg.kind, timestamp=msg.timestamp))
                else:
                    pydantic_ai_history.append(msg)
        except Exception:
            pydantic_ai_history = []
        try:
            result = await newsfoundry_agent.run(
                message.content, 
                deps=AgentDeps(system_prompt=chat.system_prompt, chat_id=chat.id),
                message_history=pydantic_ai_history
            )
            response_content = ""
            for msg in result.new_messages():
                if isinstance(msg, ModelResponse):
                    for part in msg.parts:
                        if isinstance(part, TextPart):
                            response_content += part.content
            chat.history = ta.dump_python(result.all_messages(), mode='json')
            session.add(chat)
            session.commit()
            return {"response": response_content}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/chats/{chat_id}/press-release")
async def create_press_release(chat_id: int, request: PressReleaseRequest, user: User = Depends(get_current_user)):
    with Session(engine) as session:
        chat = session.get(Chat, chat_id)
        if not chat or chat.user_id != user.id:
            raise HTTPException(status_code=403)
        
        new_release_dict = None
        if chat.loaded_articles:
            try:
                release_data = await generate_rag_press_release(chat.loaded_articles, request.topic)
                new_release_dict = release_data.model_dump()
            except Exception as e:
                print(f"⚠️ RAG fail: {e}")

        if not new_release_dict:
            ta = TypeAdapter(list[ModelMessage])
            try:
                pydantic_ai_history = ta.validate_python(chat.history)
                result = await press_agent.run(f"Rédige une revue de presse sur : {request.topic}", message_history=pydantic_ai_history)
                new_release_dict = result.output.model_dump()
            except Exception as e:
                raise HTTPException(status_code=500, detail="Échec génération")

        current_releases = list(chat.press_releases)
        current_releases.append(new_release_dict)
        chat.press_releases = current_releases
        session.add(chat)
        session.commit()
        return new_release_dict

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
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)