
import os
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
import bcrypt

TEST_DB_FILE = "./test_backend.db"

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # On supprime l'ancienne base de données de test pour repartir sur un schéma tout neuf
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)

    os.environ["MISTRAL_API_KEY"] = "mock_key_only_for_tests"
    os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_FILE}"

    from database import init_db
    
    # Initialisation des tables sur le fichier tout neuf
    init_db()
    
    yield
    
    # Nettoyage après les tests
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)

@pytest.fixture
def client():
    from main import app
    return TestClient(app)

@pytest.fixture
def user1_token(client):
    response = client.post("/login", json={"email": "test@test.com", "password": "test"})
    token = response.json().get("access_token")
    assert token is not None, "Login failed pour user1, assurez-vous que la BDD est initialisée."
    return token

@pytest.fixture
def user2_token(client):
    from database import engine
    from models import User
    
    with Session(engine) as session:
        user2 = session.exec(select(User).where(User.email == "voleur@test.com")).first()
        if not user2:
            hashed_pw = bcrypt.hashpw("voleur".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            user2 = User(email="voleur@test.com", hashed_password=hashed_pw)
            session.add(user2)
            session.commit()
            
    response = client.post("/login", json={"email": "voleur@test.com", "password": "voleur"})
    token = response.json().get("access_token")
    assert token is not None, "Login failed pour user2."
    return token


def test_chat_workflow(client, user1_token):
    headers = {"Authorization": f"Bearer {user1_token}"}
    
    # 1. Création d'un chat
    response = client.post("/chats", headers=headers)
    assert response.status_code == 200
    chat_id = response.json()["id"]
    
    # 2. Vérification que l'historique est vide au début
    response = client.get(f"/chats/{chat_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["messages"] == []

    from agent import newsfoundry_agent
    from pydantic_ai.models.test import TestModel
    test_model = TestModel()
    
    with newsfoundry_agent.override(model=test_model):
        response = client.post(
            f"/chats/{chat_id}/messages", 
            headers=headers, 
            json={"content": "Peux-tu m'aider ?"}
        )
        assert response.status_code == 200
        assert "response" in response.json()
        
        # 3. Vérifier que l'historique contient bien l'échange
        response = client.get(f"/chats/{chat_id}", headers=headers)
        assert response.status_code == 200
        history = response.json()["messages"]
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Peux-tu m'aider ?"
        assert history[1]["role"] == "model"


def test_unauthorized_access(client, user1_token, user2_token):
    headers_user1 = {"Authorization": f"Bearer {user1_token}"}
    headers_user2 = {"Authorization": f"Bearer {user2_token}"}
    
    response_create = client.post("/chats", headers=headers_user1)
    chat_id = response_create.json()["id"]
    
    # Test d'accès du user2 au chat du user1
    response_hack = client.get(f"/chats/{chat_id}", headers=headers_user2)
    assert response_hack.status_code == 403 