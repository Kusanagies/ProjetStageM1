# On utilise la version 3.12 (identique à votre environnement local)
FROM python:3.12-slim

# Définir le répertoire de travail principal dans le conteneur
WORKDIR /app

# 1. Copier le fichier requirements.txt depuis la racine du projet
COPY requirements.txt .

# 2. Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copier le dossier src/ dans le conteneur
# On copie depuis mcp-invalidator/src vers /app/src
COPY mcp-invalidator/src/ ./src/

# 4. Se placer dans le dossier source pour que Python trouve vos fichiers
WORKDIR /app/src

# 5. Lancer le serveur MCP en mode stdio
CMD ["python", "server.py"]