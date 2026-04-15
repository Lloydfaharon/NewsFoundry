FROM ghcr.io/astral-sh/uv:python3.13-bookworm

# Le dossier de travail dans le conteneur
WORKDIR /app

# On retire "backend/" car Railway est déjà positionné dans ce dossier
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# On copie le contenu de local "src/" vers le "src/" du conteneur
COPY src/ ./src/

EXPOSE 8000

# On lance uvicorn en utilisant 'uv run' pour respecter ton environnement
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]