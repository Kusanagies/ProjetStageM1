from mcp.server.fastmcp import FastMCP
import subprocess
import tempfile
import json
import os
import shutil

# Nom du serveur MCP
mcp = FastMCP("MCP-Prover")

@mcp.tool()
def verify_lean_proof(conjecture_id: str, lean_code: str) -> str:
    """
    Vérifie formellement une preuve ou une formalisation écrite en Lean 4.
    
    Args:
        conjecture_id: L'identifiant de la conjecture (ex: "T1").
        lean_code: Le code source complet en langage Lean 4 à compiler.
        
    Returns:
        Un JSON contenant le statut (success, incomplete, error) et les messages du compilateur.
    """
    # 1. Création d'un fichier temporaire pour Lean
    with tempfile.NamedTemporaryFile(suffix=".lean", delete=False, mode="w", encoding="utf-8") as temp_file:
        temp_file.write(lean_code)
        filepath = temp_file.name

    try:
        
        lean_executable = shutil.which("lean") or "/root/.elan/bin/lean"
        # 2. Exécution du compilateur Lean 4
        # On capture la sortie standard (stdout) et les erreurs (stderr)
        process = subprocess.run(
            [lean_executable, filepath], 
            capture_output=True, 
            text=True
        )
        
        output = process.stdout + process.stderr
        
        # 3. Analyse stricte du résultat (conformément au sujet de stage)
        has_errors = process.returncode != 0
        uses_sorry = "sorry" in lean_code or "declaration uses 'sorry'" in output
        
        if has_errors:
            status = "error"
            message = "Le fichier Lean contient des erreurs de compilation ou la preuve est fausse."
        elif uses_sorry:
            status = "incomplete"
            message = "Le fichier compile, mais la preuve contient des 'sorry'. Elle est incomplète."
        else:
            status = "success"
            message = "Félicitations ! La preuve est complète et formellement vérifiée par Lean 4."

        # 4. Formatage de la réponse
        response = {
            "conjecture_id": conjecture_id,
            "status": status,
            "message": message,
            "compiler_output": output, # Permettra au LLM de lire ses erreurs pour se corriger
            "metrics": {
                "has_errors": has_errors,
                "uses_sorry": uses_sorry
            }
        }
        
        return json.dumps(response, indent=2)

    except FileNotFoundError:
        return json.dumps({
            "conjecture_id": conjecture_id,
            "status": "error",
            "message": "Le compilateur 'lean' n'est pas installé ou n'est pas dans le PATH du serveur.",
            "compiler_output": "",
            "metrics": {"has_errors": True, "uses_sorry": False}
        }, indent=2)
    finally:
        # Nettoyage du fichier temporaire
        if os.path.exists(filepath):
            os.remove(filepath)

if __name__ == "__main__":
    mcp.run()