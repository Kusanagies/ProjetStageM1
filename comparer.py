import json
import sys
import os
import networkx as nx
import random

sys.path.append(os.path.join(os.path.dirname(__file__), 'mcp-invalidator', 'src'))

from verifier import IndependentVerifier
from invalidator import ConjectureEvaluator, Invalidator, GraphMutator

def mutate_generique(G, max_mutations=2):
    mutated = G.copy()
    funcs = [
        GraphMutator._mutation_add_edge,
        GraphMutator._mutation_remove_edge,
        GraphMutator._mutation_add_vertex,
        GraphMutator._mutation_remove_vertex,
        GraphMutator._mutation_replace_by_star,
    ]
    for _ in range(random.randint(1, max_mutations)):
        mutated = random.choice(funcs)(mutated)
    return mutated

def restart_generique(g_class):
    return nx.erdos_renyi_graph(random.randint(5, 12), 0.4)

def run_search(conj, mutate_fn, restart_fn, timeout=15, max_iterations=5000, stagnation_limit=20, neighbor_count=15):
    import time
    from invalidator import GraphScoreCache

    evaluator = ConjectureEvaluator(conj)
    cache = GraphScoreCache()
    g_class = conj.get("graph_class", "connected")

    if mutate_fn == mutate_generique:
        current = nx.path_graph(5)
    else:
        _, current = Invalidator(evaluator)._get_mutator_and_start()

    current_score = evaluator.calculate_score(current)
    best_score = current_score
    no_improve = 0
    start = time.time()

    for iteration in range(max_iterations):
        elapsed = time.time() - start
        if elapsed > timeout:
            return "Non trouve", round(elapsed, 2)
        if current_score < 0:
            return "Trouve", round(elapsed, 2)

        voisins = []
        for _ in range(neighbor_count):
            try:
                candidat = mutate_fn(current, max_mutations=3)
                score = evaluator.calculate_score(candidat)
                if score != float('inf'):
                    voisins.append((candidat, score))
            except Exception:
                continue

        if not voisins:
            no_improve += 1
            continue

        meilleur, meilleur_score = min(voisins, key=lambda x: x[1])

        if meilleur_score <= current_score:
            current = meilleur
            current_score = meilleur_score
            if meilleur_score < best_score:
                best_score = meilleur_score
                no_improve = 0
            else:
                no_improve += 1
        else:
            no_improve += 1

        if no_improve >= stagnation_limit:
            current = restart_fn(g_class)
            current_score = evaluator.calculate_score(current)
            no_improve = 0

    elapsed = time.time() - start
    return "Non trouve", round(elapsed, 2)

def get_mutateur_nouveau(g_class):
    if g_class == "tree":
        return GraphMutator.mutate_tree
    elif g_class == "planar":
        return GraphMutator.mutate_planar
    elif g_class == "bipartite":
        return GraphMutator.mutate_bipartite
    else:
        return GraphMutator.mutate

def restart_nouveau(g_class):
    if g_class == "tree":
        return nx.random_labeled_tree(random.randint(4, 10))
    elif g_class == "planar":
        G = nx.path_graph(random.randint(4, 10))
        for _ in range(5):
            G = GraphMutator._planar_add_edge(G)
        return G
    elif g_class == "bipartite":
        return nx.complete_bipartite_graph(random.randint(2, 6), random.randint(2, 6))
    else:
        return nx.erdos_renyi_graph(random.randint(5, 12), 0.4)

def main():
    with open('data/benchmark_test.json', 'r') as f:
        conjectures = json.load(f)

    TIMEOUT = 60

    print(f"\nComparaison sur {len(conjectures)} conjectures (timeout {TIMEOUT}s chacune)")
    print("=" * 72)
    print(f"{'ID':<12} {'Classe':<12} {'Ancien':^14} {'Nouveau':^14} {'Diff':^8}")
    print("-" * 72)

    resultats = []

    for conj in conjectures:
        cid = conj['id']
        g_class = conj.get('graph_class', 'connected')

        statut_ancien, t_ancien = run_search(
            conj, mutate_generique, restart_generique, timeout=TIMEOUT
        )

        mutateur_nouveau = get_mutateur_nouveau(g_class)
        statut_nouveau, t_nouveau = run_search(
            conj, mutateur_nouveau, restart_nouveau, timeout=TIMEOUT
        )

        if statut_ancien == "Non trouve" and statut_nouveau == "Trouve":
            diff = "<-- GAIN"
        elif statut_ancien == "Trouve" and statut_nouveau == "Non trouve":
            diff = "REGRESSION"
        else:
            diff = ""

        ancien_str = f"Trouve ({t_ancien}s)" if statut_ancien == "Trouve" else f"Non trouve"
        nouveau_str = f"Trouve ({t_nouveau}s)" if statut_nouveau == "Trouve" else f"Non trouve"

        print(f"{cid:<12} {g_class:<12} {ancien_str:^14} {nouveau_str:^14} {diff:^8}")
        resultats.append((cid, g_class, statut_ancien, statut_nouveau))

    print("=" * 72)

    classes = sorted(set(r[1] for r in resultats))
    print("\nBilan par classe :")
    for cls in classes:
        sous = [r for r in resultats if r[1] == cls]
        total = len(sous)
        ancien_ok = sum(1 for r in sous if r[2] == "Trouve")
        nouveau_ok = sum(1 for r in sous if r[3] == "Trouve")
        print(f"  {cls:<12} : ancien {ancien_ok}/{total}  ->  nouveau {nouveau_ok}/{total}")

    gains = sum(1 for r in resultats if r[2] == "Non trouve" and r[3] == "Trouve")
    regs  = sum(1 for r in resultats if r[2] == "Trouve" and r[3] == "Non trouve")
    print(f"\nGains   : +{gains} conjectures resolues en plus")
    print(f"Regressions : {regs}")

if __name__ == "__main__":
    main()
