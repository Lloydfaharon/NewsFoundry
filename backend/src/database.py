import os
from .models import User
from sqlmodel import SQLModel, Session, create_engine, select
import bcrypt

# 1. Récupération de la variable d'environnement
DATABASE_URL = os.getenv("DATABASE_URL")

# 2. Vérification et Correction du protocole pour SQLAlchemy
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 3. Création du moteur (avec une sécurité si l'URL est manquante)
if not DATABASE_URL:
    # Cela affichera une erreur claire dans les logs Railway
    raise ValueError("Erreur : La variable DATABASE_URL est vide ou introuvable.")

engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    # Création des tables
    SQLModel.metadata.create_all(engine)
    print("Database initialized successfully")

    # Création d'un utilisateur par défaut pour les tests
    default_email = "test@test.com"
    default_password = "test"

    with Session(engine) as session:
        statement = select(User).where(User.email == default_email)
        user = session.exec(statement).first()

        if not user:
            # On hash le mot de passe proprement
            salt = bcrypt.gensalt()
            hashed_pw = bcrypt.hashpw(default_password.encode("utf-8"), salt)
            
            # On décode en utf-8 pour le stockage en base si le champ est une String
            new_user = User(
                email=default_email,
                hashed_password=hashed_pw.decode("utf-8")
            )
            
            session.add(new_user)
            session.commit()
            print("Utilisateur par défaut créé avec succès.")
