import sys
import os
import json
import csv
import time

# Ajout du dossier src au chemin de recherche
sys.path.append(os.path.join(os.path.dirname(__file__), 'mcp-invalidator', 'src'))

from verifier import IndependentVerifier
from invalidator import ConjectureEvaluator, Invalidator

def run_campaign():
    input_file = 'data/benchmark_test.json'
    output_file = 'data/resultats_campagne.csv'
    
    # Paramètres de l'expérience (à mentionner dans votre rapport)
    MAX_ITER = 10000
    TIMEOUT = 30.0

    print("Lancement de la campagne d'expérimentation...")

    with open(input_file, 'r') as f:
        conjectures = json.load(f)

    # Préparation du fichier CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'ID', 'Classe', 'Invariant_Gauche', 'Relation', 'Temps_Sec', 
            'Iterations', 'Statut', 'Graphe_Trouve_g6', 'Faux_Positif_Rejete'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for conj in conjectures:
            print(f"Test de la conjecture : {conj['id']}...")
            
            evaluator = ConjectureEvaluator(conj)
            search_engine = Invalidator(evaluator)
            
            # Lancement chronométré
            start_time = time.time()
            result = search_engine.search(max_iterations=MAX_ITER, timeout_seconds=TIMEOUT)
            real_time = round(time.time() - start_time, 3)
            
            row = {
                'ID': conj['id'],
                'Classe': conj.get('graph_class', 'connected'),
                'Invariant_Gauche': conj['inequality']['left_invariant'],
                'Relation': conj['inequality']['relation'],
                'Temps_Sec': real_time,
                'Iterations': result.get('iterations', MAX_ITER),
                'Graphe_Trouve_g6': '',
                'Faux_Positif_Rejete': 'Non'
            }

            if result["status"] == "counterexample_found":
                found_g6 = result["value"]
                # Vérification rigoureuse par la Tâche 4
                verif_result = IndependentVerifier.verify(conj, found_g6)
                
                if verif_result.get("is_valid_counterexample"):
                    row['Statut'] = 'Succès'
                    row['Graphe_Trouve_g6'] = found_g6
                else:
                    row['Statut'] = 'Échec (Rejeté)'
                    row['Faux_Positif_Rejete'] = 'Oui'
            else:
                row['Statut'] = f"Timeout ({result.get('reason')})"

            writer.writerow(row)
            # Force l'écriture sur le disque à chaque étape en cas de crash
            csvfile.flush() 

    print(f"Campagne terminée. Les résultats sont sauvegardés dans {output_file}.")

if __name__ == "__main__":
    run_campaign()