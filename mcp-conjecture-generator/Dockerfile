FROM python:3.12-slim

WORKDIR /app

# 1. Copier le fichier requirements spécifique au générateur depuis la racine
COPY mcp-conjecture-generator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Copier le dossier src en précisant son chemin complet
COPY mcp-conjecture-generator/src/ ./src/

WORKDIR /app/src

# 3. Lancer le serveur
CMD ["python", "server.py"]