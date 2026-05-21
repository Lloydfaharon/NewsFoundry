# Documentation Technique - NewsFoundry

## 0. Présentation du projet

NewsFoundry est une plateforme de veille informationnelle augmentée par l'Intelligence Artificielle. Elle permet non seulement de suivre l'actualité mondiale en temps réel, mais transforme l'expérience utilisateur grâce à un agent conversationnel capable de naviguer sur le web pour approfondir des sujets complexes. La force de l'outil réside dans sa capacité à synthétiser des volumes massifs de données en revues de presse structurées et personnalisées, offrant ainsi une solution complète de gestion de l'information.

Lien du site web : https://news-foundry.vercel.app/

## 1. Structure du Projet

L'application **NewsFoundry** est construite sur une architecture client-serveur moderne, séparant clairement les responsabilités entre l'interface utilisateur et la logique métier.

```text
newsfoundry/
├── frontend/                 # Interface Utilisateur (Next.js)
│   └── app/                  # App Router
│       ├── chat/             # Page de l'agent conversationnel
│       ├── component/        # Composants React réutilisables
│       ├── login/            # Page de connexion
│       ├── revue/            # Page des revues de presse
│       └── globals.css       # Styles globaux TailwindCSS
│
└── backend/                  # Logique Métier & IA (FastAPI)
    ├── src/
    │   ├── main.py           # Point d'entrée de l'API (Routes FastAPI)
    │   ├── models.py         # Schémas de base de données (SQLModel)
    │   ├── agent.py          # Configuration de l'agent conversationnel (PydanticAI)
    │   ├── press_service.py  # Logique RAG pour la revue de presse (LlamaIndex)
    │   ├── news_service.py   # Intégration de l'API WorldNewsAPI
    │   └── auth.py           # Logique d'authentification (JWT, bcrypt)
    ├── tests/                # Tests unitaires et d'intégration (Pytest)
    └── test_backend.db       # Base de données SQLite (environnement local/test)
```


## 2. Justification des Choix Techniques

### Frontend
- **Next.js (App Router) & React :** Choisi pour sa performance, son rendu hybride (Client/Serveur) et sa gestion native et intuitive du routage (`/login`, `/chat`, `/revue`).
- **Tailwind CSS :** Permet un développement d'interface ultra-rapide et garantit la conformité exacte avec les maquettes Figma grâce à ses classes utilitaires et sa facilité à créer des designs responsives.

### Backend
- **FastAPI :** Ce framework Python a été sélectionné pour sa rapidité d'exécution, sa prise en charge native de l'asynchrone (`async`/`await` indispensable pour les appels aux LLMs et aux API externes), et sa validation automatique des données via Pydantic.
- **SQLModel (sur SQLite/PostgreSQL) :** Combine la puissance de SQLAlchemy et la simplicité de Pydantic. Cela évite d'avoir à dupliquer les modèles de données (un pour la BDD, un pour l'API).
- **Authentification JWT & bcrypt :** Standard industriel robuste. Il permet une architecture *stateless* (sans état) où le frontend gère son token en toute autonomie (stockage en `localStorage`).

### Intelligence Artificielle & RAG
- **PydanticAI (pour le Chatbot) :** Permet de créer des Agents de manière très propre en Python en injectant des dépendances (`AgentDeps`) et en déclarant des outils (Tools) natifs de manière asynchrone.
- **LlamaIndex (pour la Revue de Presse) :** Outil redoutable pour le *Retrieval-Augmented Generation* (RAG). Son utilisation du `SimpleWebPageReader` permet de scraper automatiquement les URLs et de les résumer. Le `SummaryIndex` a été choisi car l'objectif est de synthétiser plusieurs articles en un seul document structuré (`PressRelease`).
- **Mistral AI :** Modèle performant (mistral-large-latest) offrant d'excellentes capacités de synthèse en français tout en respectant strictement les formats JSON demandés.

---

## 3. Gestion des Erreurs de l'API Backend

Le backend utilise les `HTTPException` de FastAPI pour renvoyer des codes d'erreur clairs, que le frontend intercepte pour afficher des bannières d'alerte à l'utilisateur.

| Code HTTP | Cas d'usage dans NewsFoundry |
| :--- | :--- |
| **`401 Unauthorized`** | - Email ou mot de passe incorrect lors du login.<br>- Token JWT manquant, expiré, ou invalide. Entraîne l'expulsion immédiate vers `/login` côté frontend. |
| **`403 Forbidden`** | - Tentative d'accès à l'historique d'une discussion (`/chats/{id}`) qui n'appartient pas à l'utilisateur authentifié (sécurité anti-vol de données). |
| **`500 Internal Server Error`** | - Défaillance lors de l'appel au modèle LLM (Mistral).<br>- Échec de génération RAG de la revue de presse (ex: format Pydantic non respecté par l'IA). |

> **Note UI :** Côté frontend, toute erreur (API tombée, 401, 500) est attrapée par des blocs `try/catch` qui déclenchent une modale rouge `showError()` affichée pendant 5 secondes pour informer l'utilisateur sans casser l'application.

---

## 4. Choix et Stratégie des Prompts

Le succès de l'application repose sur un "Prompt Engineering" rigoureux, adapté à chaque contexte.

### A. Le Prompt Système du Chatbot (Agent Conversationnel)
Situé dans `main.py`, ce prompt est injecté à la création de chaque nouvelle discussion :
> *"Tu es l'assistant de NewsFoundry, une application destinée à la gestion d'articles. Réponds systématiquement en utilisant le format Markdown. Si l'utilisateur pose une question sur un sujet qui n'est pas mentionné dans le contexte d'actualités ci-dessous, réponds poliment que tu n'as pas d'informations récentes à ce sujet aujourd'hui, afin de ne pas le laisser sans réponse. [INJECTION DES ACTUALITÉS DU JOUR]"*

**Raisons de ce choix :**
- **Persona défini :** Donne un ton professionnel et un cadre à l'IA.
- **Formatage forcé :** Le Markdown garantit que l'interface ReactMarkdown du frontend s'affiche proprement avec des listes et du gras.
- **Anti-Hallucination et Politesse :** En demandant explicitement à l'IA d'avouer poliment son ignorance si un sujet n'est pas dans l'actualité du jour, on évite qu'elle n'invente des faits ou ne réponde de manière abrupte.

### B. Le Prompt RAG (Génération de Revue de Presse)
Situé dans `press_service.py` via LlamaIndex :
> *"Rédige une revue de presse structurée et professionnelle sur le sujet : {topic}. Utilise EXCLUSIVEMENT les informations trouvées dans les articles fournis. Pour chaque article pertinent, rédige un résumé détaillé et captivant."*

**Raisons de ce choix :**
- **Contrainte stricte (EXCLUSIVEMENT) :** C'est le cœur du RAG. On force le modèle à se baser uniquement sur le texte scrappé par LlamaIndex, bloquant ainsi ses connaissances internes potentiellement obsolètes.
- **Guidage de structure :** Le prompt est couplé à un argument `response_format=PressRelease` dans LlamaIndex. Cela garantit que la réponse du modèle ne sera pas du texte libre, mais un objet JSON strict (titre, résumé global, articles) que le frontend peut parser sans erreur.

---

## 5. Prérequis et Lancement du Projet

L'application est séparée en deux environnements distincts.

### Frontend (Interface Web)
- **Prérequis :** Node.js installé.
- **Lancement :**
  ```bash
  cd frontend
  npm install
  npm run dev
  ```
  Le site sera accessible sur `http://localhost:3000`.

### Backend (Serveur API)
- **Prérequis :** Python 3.12+ et le gestionnaire `uv`.
- **Lancement :**
  ```bash
  cd backend
  uv sync
  uv run uvicorn src.main:app --reload
  ```
  L'API sera accessible sur `http://localhost:8000`.

---

## 6. Variables d'Environnement (`.env`)

Pour fonctionner correctement, l'application a besoin de clés secrètes. 

**Côté Backend (fichier `backend/.env`) :**
- `MISTRAL_API_KEY` : Clé secrète pour communiquer avec l'IA Mistral.
- `WORLD_NEWS_API_KEY` : Clé pour chercher les articles d'actualité en temps réel.
- `SECRET_KEY` : Chaîne de caractères aléatoire complexe utilisée pour chiffrer les tokens JWT de sécurité.
- `DATABASE_URL` : URL de connexion à la base de données (ex: `sqlite:///./newsfoundry.db` en local, ou `postgresql://...` en production).

**Côté Frontend (fichier `frontend/.env.local`) :**
- `NEXT_PUBLIC_API_URL` : Permet au front de savoir où contacter le backend (ex: `http://localhost:8000`).

---

## 7. Schéma de la Base de Données

Le backend utilise SQLModel. L'architecture des données repose principalement sur deux tables relationnelles :

1. **Table `User` :** 
   - Contient l'ID, l'Email, et le mot de passe hashé (via `bcrypt`).
2. **Table `Chat` :** 
   - Reliée à `User` (clé étrangère `user_id`). 
   - Contient un ID, le prompt système généré, la date de création (`created_at`), l'historique JSON des messages, et la liste des URLs scrappées (`loaded_articles`) pour le RAG.

Cette séparation stricte garantit qu'un utilisateur (User) ne peut lire que les discussions (Chat) qui lui appartiennent.

---

## 8. Automatisation et Tests (CI/CD)

Pour garantir la stabilité du code à chaque nouvelle fonctionnalité, un pipeline CI/CD est en place.
- **Pytest :** Les tests unitaires sont écrits avec Pytest (ex: `tests/test_chat.py`) pour tester les workflows critiques (Création d'un chat, Vérification de la sécurité anti-piratage d'un autre utilisateur).
- **GitHub Actions :** Un fichier `.github/workflows/pytest.yml` est configuré pour lancer automatiquement la commande de test sur les serveurs de GitHub à chaque nouveau "push" de code. Si un test échoue (ex: une faille de sécurité s'est glissée dans le code), le code est rejeté.

---

## 9. Déploiement et Production

L'application a été conçue pour être "Production-Ready" en séparant l'hébergement du front et du back sur des plateformes spécialisées.

- **Frontend (Vercel) :** L'interface utilisateur développée en Next.js est déployée sur Vercel. C'est la plateforme native de Next.js, offrant une intégration continue (CI/CD) parfaite avec GitHub et des performances optimales (Edge Network).
- **Backend & Base de Données (Railway) :** L'API FastAPI et la base de données PostgreSQL de production sont hébergées sur Railway. Ce choix permet de centraliser facilement les variables d'environnement (`.env` remplacé par les paramètres secrets de Railway) et de provisionner une base de données robuste en quelques clics sans toucher au code source grâce à SQLModel.
