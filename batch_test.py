import json
import os
import sys
import time

sys.path.append(os.path.join(os.path.dirname(__file__), 'mcp-invalidator', 'src'))

from verifier import IndependentVerifier
from invalidator import ConjectureEvaluator, Invalidator, GraphInvariants, GraphMutator
import networkx as nx

def _ok(label):
    print(f"    ✓  {label}")

def _fail(label, detail=""):
    print(f"    ✗  {label}")
    if detail:
        print(f"       {detail}")

def _header(title):
    print(f"\n  [{title}]")

def run_unit_tests():
    print(" TESTS UNITAIRES")
    print("="*50)

    with open('data/benchmark_test.json', 'r') as f:
        conjectures = json.load(f)
    hdr001 = next(c for c in conjectures if c['id'] == 'HDR-001')

    G_connexe    = nx.path_graph(5)
    G_deconnecte = nx.Graph(); G_deconnecte.add_edges_from([(0,1),(2,3)])
    G_vide       = nx.Graph()

    errors = []

    def check(label, condition, detail=""):
        if condition:
            _ok(label)
        else:
            _fail(label, detail)
            errors.append(label)

    _header("GraphInvariants")

    invs = GraphInvariants.calculate_all(G_connexe)
    check("n=5, m=4 sur path(5)",       invs['n'] == 5 and invs['m'] == 4)
    check("density entre 0 et 1",       0.0 <= invs['density'] <= 1.0)
    check("rad=2, diam=4 sur path(5)",  invs.get('rad') == 2 and invs.get('diam') == 4)
    check("delta <= Delta",             invs['delta'] <= invs['Delta'])

    invs_dc = GraphInvariants.calculate_all(G_deconnecte)
    check("rad=inf sur graphe déconnecté",  invs_dc.get('rad') == float('inf'))
    check("diam=inf sur graphe déconnecté", invs_dc.get('diam') == float('inf'))

    invs_vide = GraphInvariants.calculate_all(G_vide)
    check("graphe vide ne plante pas",  isinstance(invs_vide, dict))

    _header("GraphMutator")

    mutated = GraphMutator.mutate(G_connexe)
    check("mutation retourne un Graph", isinstance(mutated, nx.Graph))

    n_avant = G_connexe.number_of_nodes()
    GraphMutator.mutate(G_connexe)
    check("mutation ne modifie pas l'original", G_connexe.number_of_nodes() == n_avant)

    G_tmp = G_connexe.copy()
    try:
        for _ in range(50):
            G_tmp = GraphMutator.mutate(G_tmp, max_mutations=3)
        check("50 mutations consécutives sans exception", isinstance(G_tmp, nx.Graph))
    except Exception as e:
        check("50 mutations consécutives sans exception", False, str(e))

    _header("IndependentVerifier")

    g6_connu = hdr001['known_counterexample']
    r = IndependentVerifier.verify(hdr001, g6_connu)
    check("accepte le contre-exemple connu de HDR-001",
          r.get('is_valid_counterexample') is True)
    check("structure de retour complète (3 clés)",
          all(k in r for k in ['is_valid_counterexample', 'hypotheses_satisfied', 'conclusion_satisfied']))

    r_corrompu = IndependentVerifier.verify(hdr001, 'XXXXXXXXXXXXXXXX')
    check("g6 corrompu → is_valid=False sans exception",
          r_corrompu.get('is_valid_counterexample') is not True)

    r_vide = IndependentVerifier.verify(hdr001, '')
    check("g6 vide → is_valid=False sans exception",
          isinstance(r_vide, dict) and r_vide.get('is_valid_counterexample') is not True)

    g6_dc = nx.to_graph6_bytes(G_deconnecte, header=False).decode('ascii').strip()
    r_dc = IndependentVerifier.verify(hdr001, g6_dc)
    check("graphe déconnecté → hypotheses_satisfied=False",
          r_dc.get('hypotheses_satisfied') is False)

    acceptes = sum(
        1 for c in conjectures
        if IndependentVerifier.verify(c, c['known_counterexample']).get('is_valid_counterexample')
    )
    check(f"benchmark : au moins 1 contre-exemple connu accepté ({acceptes} acceptés)", acceptes > 0)

    _header("ConjectureEvaluator")

    ev = ConjectureEvaluator(hdr001)
    score_ok = ev.calculate_score(nx.path_graph(3))
    check("score >= 0 pour graphe non-violant", score_ok >= 0 or score_ok == float('inf'))
    check("score = inf pour graphe hors-classe", ev.calculate_score(G_deconnecte) == float('inf'))
    check("check_graph_class: connexe=True, déconnecté=False",
          ev.check_graph_class(G_connexe) is True and ev.check_graph_class(G_deconnecte) is False)

    _header("Invalidator")

    ev = ConjectureEvaluator(hdr001)
    inv = Invalidator(ev)
    r_inv = inv.search(max_iterations=5000, timeout_seconds=30)
    check("trouve un contre-exemple sur HDR-001",
          r_inv['status'] == 'counterexample_found',
          f"statut={r_inv['status']}, raison={r_inv.get('reason')}")

    if r_inv['status'] == 'counterexample_found':
        verif_croise = IndependentVerifier.verify(hdr001, r_inv['value'])
        check("le graphe trouvé passe le vérificateur",
              verif_croise.get('is_valid_counterexample') is True)
        check("score < 0 pour un vrai contre-exemple", r_inv.get('score', 0) < 0)
        check("time_seconds présent et >= 0", r_inv.get('time_seconds', -1) >= 0)

    debut = time.time()
    inv.search(max_iterations=999999, timeout_seconds=2)
    duree = time.time() - debut
    check(f"timeout respecté (2s demandées, {duree:.1f}s réelles)", duree < 6)

    print()
    if errors:
        print(f"  BILAN : {len(errors)} test(s) échoué(s) :")
        for e in errors:
            print(f"    - {e}")
    else:
        print("  BILAN : tous les tests unitaires sont passés.")
    print("="*50)

def run_batch_tests():
    with open('data/benchmark_test.json', 'r') as f:
        conjectures = json.load(f)

    print(" DÉBUT DE LA CAMPAGNE DE TEST DU BENCHMARK HDR")
    print("="*50)

    for conj in conjectures:
        print(f"\n▶ TEST DE LA CONJECTURE : {conj['id']}")

        print("  [A] Vérification du contre-exemple connu...")
        known_g6 = conj["known_counterexample"]
        verif_result = IndependentVerifier.verify(conj, known_g6)

        if verif_result.get("is_valid_counterexample"):
            print(f"       Succès : Le graphe connu ({known_g6}) invalide bien la conjecture !")
        else:
            print(f"       Échec : Le vérificateur rejette le graphe connu. Raison : {verif_result}")

        print("  [B] Lancement de l'invalidateur heuristique...")
        evaluator = ConjectureEvaluator(conj)
        search_engine = Invalidator(evaluator)

        result = search_engine.search(max_iterations=10000, timeout_seconds=30)

        if result["status"] == "counterexample_found":
            found_g6 = result["value"]
            temps = result["time_seconds"]
            print(f"       SUCCÈS : Contre-exemple trouvé en {temps}s !")
            print(f"       Graphe trouvé (g6) : {found_g6}")
            if found_g6 != known_g6:
                print("         (Note : L'algorithme a trouvé un contre-exemple DIFFÉRENT du HDR !)")
        else:
            print(f"       ÉCHEC : Aucun contre-exemple trouvé en {result.get('time_seconds', 30)}s.")
            print(f"         Raison : {result.get('reason')}")

if __name__ == "__main__":
    run_unit_tests()
    run_batch_tests()
