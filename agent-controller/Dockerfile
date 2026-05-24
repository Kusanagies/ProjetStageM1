FROM python:3.12-slim

WORKDIR /app

# 1. Installation du client Docker CLI
RUN apt-get update && apt-get install -y docker.io && rm -rf /var/lib/apt/lists/*

# 2. Installation des dépendances de l'Agent
COPY agent-controller/requirements.txt ./agent-controller/
RUN pip install --no-cache-dir -r agent-controller/requirements.txt

# 3. Copie du code de l'Agent uniquement
COPY agent-controller/ ./agent-controller/

WORKDIR /app/agent-controller

CMD ["python", "controller.py"]