# Utilisation d'une image de base standard (Ubuntu) pour faciliter l'installation de Lean
FROM python:3.12-slim

# 1. Installation des dépendances système requises par Lean
RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/*

# 2. Installation de elan (Lean version manager) et de Lean 4
ENV ELAN_HOME="/root/.elan"
ENV PATH="${ELAN_HOME}/bin:${PATH}"

RUN curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh -s -- -y --default-toolchain leanprover/lean4:stable

# 3. Préparation de l'environnement Python
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copie du code
COPY mcp-prover/src/ ./src/

WORKDIR /app/src

# 5. Lancement du serveur MCP
CMD ["python", "server.py"]