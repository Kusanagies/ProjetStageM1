import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'mcp-invalidator', 'src'))

from verifier import IndependentVerifier
from invalidator import ConjectureEvaluator, Invalidator
import time

def run_batch_tests():
    # 1. Charger le lot de conjectures
    with open('data/benchmark_test.json', 'r') as f:
        conjectures = json.load(f)

    print("="*50)
    print(" DÉBUT DE LA CAMPAGNE DE TEST DU BENCHMARK HDR")
    print("="*50)

    for conj in conjectures:
        print(f"\n▶ TEST DE LA CONJECTURE : {conj['id']}")
        
        # --- ÉTAPE A : Test du vérificateur indépendant (Tâche 4) ---
        print("  [A] Vérification du contre-exemple connu...")
        known_g6 = conj["known_counterexample"]
        verif_result = IndependentVerifier.verify(conj, known_g6)
        
        if verif_result.get("is_valid_counterexample"):
            print(f"       Succès : Le graphe connu ({known_g6}) invalide bien la conjecture !")
        else:
            print(f"       Échec : Le vérificateur rejette le graphe connu. Raison : {verif_result}")

        # --- ÉTAPE B : Test de votre moteur de recherche locale (Tâche 3) ---
        print("  [B] Lancement de l'invalidateur heuristique...")
        evaluator = ConjectureEvaluator(conj)
        search_engine = Invalidator(evaluator)
        
        # On donne un temps limité (ex: 30 secondes par conjecture)
        result = search_engine.search(max_iterations=10000, timeout_seconds=30)
        
        if result["status"] == "counterexample_found":
            found_g6 = result["value"]
            temps = result["time_seconds"]
            print(f"       SUCCÈS : Contre-exemple trouvé en {temps}s !")
            print(f"       Graphe trouvé (g6) : {found_g6}")
            
            # Si le graphe trouvé est différent de celui du benchmark, on le précise
            if found_g6 != known_g6:
                print("         (Note : L'algorithme a trouvé un contre-exemple DIFFÉRENT du HDR !)")
        else:
            print(f"       ÉCHEC : Aucun contre-exemple trouvé en {result.get('time_seconds', 30)}s.")
            print(f"         Raison : {result.get('reason')}")

if __name__ == "__main__":
    run_batch_tests()