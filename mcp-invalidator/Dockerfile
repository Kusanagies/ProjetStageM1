# Utiliser une image Python officielle légère
FROM python:3.10-slim

WORKDIR /app

# Copier et installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier TOUT le code source du dossier
COPY /src/invalidator.py .
COPY /src/server.py .

# La commande par défaut lance désormais le serveur MCP
CMD ["python", "server.py"]