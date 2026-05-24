# Agent Prouveur - MCP & LLM pour la Theorie des Graphes

Ce projet s'inscrit dans le cadre d'un stage de Master 1 MIAGE. Il vise a concevoir un environnement modulaire de decouverte mathematique assistee par ordinateur. Un agent autonome, propulse par un Modele de Langage (LLM), orchestre plusieurs outils specialises via le protocole **MCP (Model Context Protocol)** pour traiter des conjectures en theorie des graphes.

L'architecture est entierement conteneurisee via **Docker**, assurant une isolation stricte entre l'IA, les heuristiques de recherche en Python et l'assistant de preuve formelle Lean 4.

---

## Architecture du Projet

Le projet est divise en quatre micro-services principaux :

1. **Agent Controleur (`agent-controller/`)** : Le chef d'orchestre. Il utilise le modele Gemma 2 (via Ollama) pour analyser les conjectures, faire appel aux bons outils MCP, et synthetiser les resultats.
2. **MCP Invalidateur (`mcp-invalidator/`)** : Utilise des algorithmes de recherche locale (Hill Climbing) pour trouver des contre-exemples (au format g6) refutant les conjectures fausses, avec une verification stricte pour eviter les faux positifs.
3. **MCP Generateur (`mcp-conjecture-generator/`)** : Propose de nouvelles inegalites plausibles entre des invariants de graphes et les filtre pour eliminer les evidences.
4. **MCP Prouveur (`mcp-prover/`)** : Encapsule le compilateur Lean 4 pour verifier formellement les preuves mathematiques (ou detecter les tricheries comme l'utilisation de `sorry`).

---

## Prerequis

Avant de lancer le projet, assurez-vous de disposer des elements suivants sur votre machine :

- **Docker** et **Docker Compose** installes.
- **Ollama** installe (pour faire tourner le LLM localement).
- Git (pour cloner le depot).

---

## Installation et Configuration

### 1. Preparer le LLM (Ollama)

L'agent a besoin d'un modele de langage pour fonctionner. Par defaut, le code utilise **Gemma**.
Ouvrez un terminal sur votre machine physique (pas dans Docker) et lancez :

```bash
# Telecharger et tester le modele
ollama run gemma4:e2b
```
(Quittez avec `/bye` une fois le modele telecharge).

**IMPORTANT - Configuration reseau :** Pour que Docker puisse communiquer avec Ollama, ce dernier doit ecouter sur toutes les interfaces reseau (`0.0.0.0`). 
Fermez completement Ollama (via la barre des taches ou `sudo systemctl stop ollama`), puis relancez-le manuellement dans un terminal qui restera ouvert en arriere-plan :

- **Sous Linux / macOS :**
  ```bash
  OLLAMA_HOST=0.0.0.0 ollama serve
  ```
- **Sous Windows (PowerShell) :**
  ```powershell
  $env:OLLAMA_HOST="0.0.0.0"; ollama serve
  ```

Vous pouvez verifier qu'Ollama est pret en visitant `http://localhost:11434` dans votre navigateur ("Ollama is running").

### 2. Cloner et construire le projet

Ouvrez un nouveau terminal a la racine du projet clone. Nous allons utiliser Docker Compose pour construire les images de tous nos outils MCP.

```bash
docker-compose --profile tools build
```
*Cette commande va creer les images `mcp-invalidator`, `mcp-generator` et `mcp-prover`. Elle peut prendre quelques minutes, notamment pour l'installation de Lean 4.*

---

## Execution

Une fois les images construites et Ollama lance en arriere-plan, vous pouvez demarrer l'Agent Controleur. 
Celui-ci va lire le fichier de test (`data/benchmark_test.json`), invoquer les conteneurs necessaires a la volee, et rediger son rapport final.

Lancez la commande suivante a la racine du projet :

```bash
docker-compose run --rm agent-controller
```

Vous devriez voir l'agent analyser la conjecture, se connecter au conteneur MCP approprie (via le socket Docker monte), et generer sa conclusion.

---

## Structure des dossiers

```text
projet/
 |- docker-compose.yml       # Declaration de l'architecture micro-services
 |- agent-controller/        # Code de l'IA et connexion a Ollama
 |- mcp-invalidator/         # Code de la recherche locale et du verificateur
 |- mcp-conjecture-generator/# Code de la generation de nouvelles inegalites
 |- mcp-prover/              # Conteneur Lean 4
 |- data/                    # Fichiers JSON (banc de test HDR, resultats CSV)
```

---

## Auteurs
- Sylvain Huang
- Hassan Jatta
- Samira Alim
