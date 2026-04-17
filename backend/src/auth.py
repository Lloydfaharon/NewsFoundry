import jwt
import os
from datetime import datetime, timedelta
from fastapi import HTTPException

# On récupère une clé secrète depuis les variables d'environnement Railway
# Si elle n'existe pas, on met une valeur par défaut (uniquement pour le dev)
SECRET_KEY = os.getenv("JWT_SECRET", "super_secret_key_provisoire")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 heures

def create_access_token(data: dict):
    """Génère un token JWT signé."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """Décode et vérifie la validité du token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalide")