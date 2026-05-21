# Utiliser une image Python officielle légère
FROM python:3.10-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier le fichier des dépendances
COPY requirements.txt .

# Installer les dépendances (sans garder le cache pour alléger l'image)
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source de l'invalidateur
COPY invalidator.py .

# Commande exécutée par défaut lors du lancement du conteneur
CMD ["python", "invalidator.py"]