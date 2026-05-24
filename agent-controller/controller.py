import asyncio
import json
import os
import requests
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# ==========================================
# 1. SIMULATION DU LLM (Agent)
# ==========================================
class LLMAgent:
    """
    Classe qui interroge le modèle Gemma 4 e2b via le serveur local Ollama.
    """
    def __init__(self, model_name="gemma4:e2b"):
        self.model = model_name
        self.api_url = "http://host.docker.internal:11434/api/generate"

    def _query_ollama(self, prompt_text):
        """Fonction interne pour envoyer la requête au serveur local Ollama."""
        payload = {
            "model": self.model,
            "prompt": prompt_text,
            "stream": False # On attend la réponse complète avant de l'afficher
        }
        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except requests.exceptions.RequestException as e:
            details = response.text if 'response' in locals() else str(e)
            return f"Erreur avec Ollama. Details : {details}"

    def analyze_conjecture(self, conjecture):
        print("\n[LLM] Interrogation de Gemma 4 en cours (cela peut prendre quelques secondes)...")
        
        prompt = f"""
        Tu es un expert en théorie des graphes. Analyse la conjecture suivante.
        ID : {conjecture.get('id')}
        Classe de graphes ciblée : {conjecture.get('graph_class')}
        Invariant à gauche : {conjecture.get('inequality', {}).get('left_invariant')}
        Expression à droite : {conjecture.get('inequality', {}).get('right_expression')}
        
        Ta tâche : Rédige une analyse stricte et très courte (2 phrases maximum). 
        Identifie les invariants et confirme qu'il faut utiliser l'invalidateur heuristique pour la tester.
        """
        
        return self._query_ollama(prompt)

    def synthesize(self, conjecture_id, invalidator_result):
        print("\n[LLM] Demande de synthèse à Gemma 4...")
        
        prompt = f"""
        Tu es un assistant scientifique de niveau Master. Résume le résultat de l'invalidateur de conjectures.
        Conjecture analysée : {conjecture_id}
        Résultat brut de l'algorithme : {invalidator_result}
        
        Ta tâche : Rédige une conclusion finale claire.
        - Si un contre-exemple a été trouvé, indique clairement que la conjecture est FAUSSE et cite le graphe (format g6).
        - Si aucun contre-exemple n'a été trouvé, indique qu'elle résiste à l'invalidation et suggère de tenter une preuve formelle avec Lean.
        Sois professionnel et direct.
        """
        
        return self._query_ollama(prompt)

# ==========================================
# 2. LE CONTROLEUR ORCHESTRATEUR
# ==========================================
async def run_controller():
    print("="*50)
    print("DEMARRAGE DE L'AGENT ORCHESTRATEUR")
    print("="*50)

    agent = LLMAgent()

    # Etape 1 : Le controleur charge une conjecture
    conjecture_test = {
        "id": "HDR-001",
        "graph_class": "connected",
        "inequality": {
            "left_invariant": "density",
            "relation": "<=",
            "right_expression": "65/98 + (18/29)*rad - (17/53)*rad**2 + (1/28)*rad**3"
        }
    }
    
    print(f"\n[Controleur] Conjecture {conjecture_test['id']} chargee.")

    # Etape 2 : Le LLM propose une strategie
    analyse = agent.analyze_conjecture(conjecture_test)
    print(f"LLM : {analyse}")

    # Etape 3 : Connexion au serveur MCP Invalidateur
    print("\n[Controleur] Connexion au serveur MCP Invalidateur...")
    
    # On pointe vers le chemin absolu de notre serveur
    server_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp-invalidator", "src", "server.py"))
    
    server_params = StdioServerParameters(
        command="docker",
        args=["run", "-i", "--rm", "mcp-invalidator"]
    )

    # Initialisation du client MCP
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("[Controleur] Appel de l'outil 'invalidate'...")
            
            # Appel de l'outil expose par notre serveur MCP
            tool_result = await session.call_tool(
                "invalidate", 
                arguments={"conjecture": conjecture_test, "timeout_seconds": 15}
            )
            
            # Le resultat renvoye par MCP est une liste de contenus (generalement du texte JSON)
            result_json = json.loads(tool_result.content[0].text)
            
            # Etape 4 & 5 : Si contre-exemple trouve (Gere par la synthese)
            # Etape 6 : Rapport court
            rapport = agent.synthesize(conjecture_test["id"], result_json)
            
            print("="*50)
            print("RAPPORT FINAL")
            print("="*50)
            print(rapport)

if __name__ == "__main__":
    # Point d'entree asynchrone
    asyncio.run(run_controller())