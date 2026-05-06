import os
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

# Injection d'une fausse clé avant l'import de PydanticAI pour que l'initialisation ne plante pas
# Nom de la base de données de test
TEST_DB_FILE = "./test_backend.db"

# On supprime l'ancienne base de données de test pour repartir sur un schéma tout neuf
if os.path.exists(TEST_DB_FILE):
    os.remove(TEST_DB_FILE)

os.environ["MISTRAL_API_KEY"] = "mock_key_only_for_tests"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_FILE}"

from main import app
from agent import newsfoundry_agent
from pydantic_ai import models
from pydantic_ai.models.test import TestModel
from database import init_db, engine
from models import User
import bcrypt

# Empêche PydanticAI de faire de vrais appels réseaux
models.ALLOW_MODEL_REQUESTS = False

# Initialisation des tables sur le fichier tout neuf
init_db()

client = TestClient(app)

def get_test_token():
    # On se connecte avec l'utilisateur test par défaut
    response = client.post("/login", json={"email": "test@test.com", "password": "test"})
    # S'il plante, ça veut dire que l'utilisateur de base n'est pas dans la BDD.
    return response.json().get("access_token")

def test_chat_workflow():
    token = get_test_token()
    assert token is not None, "Login failed, assurez-vous que la BDD est initialisée."
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Création d'un chat
    response = client.post("/chats", headers=headers)
    assert response.status_code == 200
    chat_id = response.json()["id"]
    
    # 2. Vérification que l'historique est vide au début
    response = client.get(f"/chats/{chat_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["messages"] == []

    test_model = TestModel()
    
    with newsfoundry_agent.override(model=test_model):
        response = client.post(
            f"/chats/{chat_id}/messages", 
            headers=headers, 
            json={"content": "Peux-tu m'aider ?"}
        )
        assert response.status_code == 200
        assert "response" in response.json()
        
        # 4. Vérifier que l'historique contient bien l'échange
        response = client.get(f"/chats/{chat_id}", headers=headers)
        assert response.status_code == 200
        history = response.json()["messages"]
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Peux-tu m'aider ?"
        assert history[1]["role"] == "model"

def get_second_test_token():
    with Session(engine) as session:
        user2 = session.exec(select(User).where(User.email == "voleur@test.com")).first()
        if not user2:
            hashed_pw = bcrypt.hashpw("voleur".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            user2 = User(email="voleur@test.com", hashed_password=hashed_pw)
            session.add(user2)
            session.commit()
    
    response = client.post("/login", json={"email": "voleur@test.com", "password": "voleur"})
    return response.json().get("access_token")

def test_unauthorized_access():
    token_user1 = get_test_token()
    headers_user1 = {"Authorization": f"Bearer {token_user1}"}
    
    token_user2 = get_second_test_token()
    headers_user2 = {"Authorization": f"Bearer {token_user2}"}
    
    response_create = client.post("/chats", headers=headers_user1)
    chat_id = response_create.json()["id"]
    
    response_hack = client.get(f"/chats/{chat_id}", headers=headers_user2)
    assert response_hack.status_code == 403
