# Utilisation de Python 3.12 pour rester cohérent avec le reste du projet
FROM python:3.12-slim

WORKDIR /app

# 1. Installer les dépendances spécifiques du contrôleur (mcp, requests)
COPY agent-controller/requirements.txt ./agent-controller/
RUN pip install --no-cache-dir -r agent-controller/requirements.txt

# 2. Installer les dépendances globales (networkx) 
# Requis car le contrôleur va lancer le script de l'invalidateur en sous-processus
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copier le code de l'invalidateur
# C'est indispensable pour que le chemin "../mcp-invalidator/src/server.py" fonctionne
COPY mcp-invalidator/ ./mcp-invalidator/

# 4. Copier le code du contrôleur
COPY agent-controller/ ./agent-controller/

# 5. Se placer dans le dossier du contrôleur
WORKDIR /app/agent-controller

# 6. Lancer l'agent
CMD ["python", "controller.py"]