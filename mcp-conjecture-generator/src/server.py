from mcp.server.fastmcp import FastMCP
import json
from generator import ConjectureGenerator

# Nom du serveur MCP
mcp = FastMCP("MCP-Conjecture-Generator")

# Instanciation du générateur
conjecture_engine = ConjectureGenerator()

@mcp.tool()
def generate_conjectures(graph_class: str = "connected", left_invariant: str = "diam", right_invariant: str = "rad", count: int = 3) -> str:
    """
    Génère des conjectures candidates (format JSON) en théorie des graphes.
    Ces conjectures ont survécu à un premier filtrage sur des graphes triviaux.
    
    Args:
        graph_class: La classe des graphes ciblée (ex: "connected", "tree").
        left_invariant: L'invariant mathématique à borner (ex: "diam", "density").
        right_invariant: L'invariant utilisé pour la borne (ex: "rad", "avg").
        count: Le nombre de conjectures à générer.
        
    Returns:
        Un tableau JSON contenant les conjectures générées au format commun.
    """
    candidates = conjecture_engine.generate(
        graph_class=graph_class, 
        left_invariant=left_invariant, 
        right_invariant=right_invariant, 
        max_results=count
    )
    
    response = {
        "status": "success",
        "generated_count": len(candidates),
        "conjectures": candidates
    }
    
    return json.dumps(response, indent=2)

if __name__ == "__main__":
    mcp.run()