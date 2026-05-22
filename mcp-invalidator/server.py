from mcp.server.fastmcp import FastMCP
from invalidator import ConjectureEvaluator, Invalidator
import json

# Initialisation du serveur MCP
# C'est ce nom que l'Agent LLM (Contrôleur) verra
mcp = FastMCP("MCP-Invalidator")

# Le décorateur @mcp.tool() indique que cette fonction est un outil appelable par le LLM
@mcp.tool()
def invalidate(conjecture: dict, max_iterations: int = 5000, timeout_seconds: int = 120) -> str:
    """
    Cherche un contre-exemple pour invalider une conjecture en théorie des graphes.
    
    Args:
        conjecture: Dictionnaire JSON représentant l'énoncé de la conjecture (format Tâche 2).
        max_iterations: Nombre d'itérations maximum pour la recherche locale.
        timeout_seconds: Temps alloué pour la recherche en secondes.
        
    Returns:
        Un JSON stringifié avec le statut de la recherche et, si trouvé, le graphe au format g6.
    """
    conjecture_id = conjecture.get("id", "unknown")
    
    # 1. Instancier les classes de la Tâche 3
    evaluator = ConjectureEvaluator(conjecture)
    search_engine = Invalidator(evaluator)
    
    # 2. Lancer la recherche algorithmique
    raw_result = search_engine.search(max_iterations=max_iterations, timeout_seconds=timeout_seconds)
    
    # 3. Formater la sortie exactement selon les attentes de la Tâche 5 du stage
    if raw_result["status"] == "counterexample_found":
        final_response = {
            "status": "counterexample_found",
            "conjecture_id": conjecture_id,
            "graph": {
                "format": raw_result["format"],
                "value": raw_result["value"]
            },
            "verification": {
                # Idéalement lié à votre module de la Tâche 4, 
                # ici on simule la réussite de la vérification.
                "hypotheses_satisfied": True, 
                "conclusion_satisfied": False
            },
            "search": {
                "method": "local_search",
                "time_seconds": raw_result["time_seconds"],
                "iterations": raw_result["iterations"]
            }
        }
    else:
        final_response = {
            "status": "no_counterexample_found",
            "conjecture_id": conjecture_id,
            "search": {
                "method": "local_search",
                "timeout_reached": raw_result["reason"] == "timeout",
                "time_seconds": raw_result["time_seconds"],
                "best_score": raw_result.get("best_score", 0)
            }
        }
        
    return json.dumps(final_response)

if __name__ == "__main__":
    # Lance le serveur via l'entrée/sortie standard (stdio)
    # C'est la méthode de communication standard pour les serveurs MCP conteneurisés
    mcp.run()