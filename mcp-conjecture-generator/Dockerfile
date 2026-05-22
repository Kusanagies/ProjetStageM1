FROM python:3.12-slim

WORKDIR /app

# Copier les dépendances spécifiques à CE serveur
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY src/ ./src/

WORKDIR /app/src

# Lancer le serveur
CMD ["python", "server.py"]