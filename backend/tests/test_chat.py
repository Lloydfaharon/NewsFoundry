import os
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

# Injection d'une fausse clé avant l'import de PydanticAI pour que l'initialisation ne plante pas
os.environ["MISTRAL_API_KEY"] = "mock_key_only_for_tests"

from src.main import app
from src.agent import newsfoundry_agent

from pydantic_ai import models
from pydantic_ai.models.test import TestModel

# Empêche PydanticAI de faire de vrais appels réseaux (sécurité pour la CI)
models.ALLOW_MODEL_REQUESTS = False

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
    assert response.json() == []

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
        history = response.json()
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Peux-tu m'aider ?"
        assert history[1]["role"] == "model"

def test_unauthorized_access():
    token = get_test_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # On essaie d'accéder au chat d'ID 99999 (qui n'existe pas ou n'appartient pas à l'user)
    response = client.get("/chats/99999", headers=headers)
    assert response.status_code == 403
