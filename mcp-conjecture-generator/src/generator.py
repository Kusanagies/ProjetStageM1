import networkx as nx
import random
import itertools

class GraphInvariants:
    """Calcul rapide des invariants pour le générateur."""
    @staticmethod
    def calc(G):
        if len(G) == 0: return {}
        n = G.number_of_nodes()
        m = G.number_of_edges()
        degrees = dict(G.degree()).values()
        
        invs = {
            "n": n, "m": m, "density": nx.density(G),
            "delta": min(degrees) if n > 0 else 0,
            "Delta": max(degrees) if n > 0 else 0,
            "avg": (2 * m / n) if n > 0 else 0
        }
        if nx.is_connected(G):
            invs["rad"] = nx.radius(G)
            invs["diam"] = nx.diameter(G)
        return invs

class ConjectureGenerator:
    """
    Générateur heuristique de conjectures.
    (À remplacer ultérieurement par le code de Thibault Anani).
    """
    def __init__(self):
        # 1. Générer un jeu de graphes de base (trivial) pour filtrer les mauvaises conjectures
        self.base_graphs = []
        for i in range(3, 10):
            self.base_graphs.append(nx.path_graph(i))
            self.base_graphs.append(nx.cycle_graph(i))
            self.base_graphs.append(nx.star_graph(i-1))
            self.base_graphs.append(nx.complete_graph(i))
            
        # Précalculer les invariants pour aller plus vite
        self.base_invariants = [GraphInvariants.calc(G) for G in self.base_graphs]

    def generate(self, graph_class="connected", left_invariant="diam", right_invariant="rad", max_results=3):
        """
        Tente de trouver des coefficients (a, b) tels que : left_invariant <= a * right_invariant + b
        qui soient vrais pour tous les graphes de base.
        """
        candidates = []
        conjecture_counter = 1
        
        # On teste des coefficients simples aléatoires ou en grille
        coefficients_a = [0.5, 1, 1.5, 2, 3]
        coefficients_b = [-2, -1, 0, 1, 2]
        
        for a, b in itertools.product(coefficients_a, coefficients_b):
            is_valid_for_all = True
            
            # Filtrage : On vérifie si l'inégalité tient sur notre jeu de graphes
            for invs in self.base_invariants:
                if left_invariant not in invs or right_invariant not in invs:
                    is_valid_for_all = False
                    break
                    
                left_val = invs[left_invariant]
                right_val = invs[right_invariant]
                
                # Test de la conjecture : Y <= a * X + b
                if left_val > (a * right_val + b):
                    is_valid_for_all = False
                    break # Fausse pour ce graphe, on jette la conjecture !
            
            # Si elle a survécu à tous les graphes de test, c'est une candidate
            if is_valid_for_all:
                expr = f"{a}*{right_invariant}" if b == 0 else f"{a}*{right_invariant} + {b}" if b > 0 else f"{a}*{right_invariant} - {abs(b)}"
                
                # Export au format JSON commun de la Tâche 2
                candidate_json = {
                    "id": f"GEN-{conjecture_counter:03d}",
                    "domain": "graph_theory",
                    "graph_class": graph_class,
                    "inequality": {
                        "left_invariant": left_invariant,
                        "relation": "<=",
                        "right_expression": expr
                    },
                    "parameters": {
                        "max_order": 30,
                        "timeout_seconds": 120
                    }
                }
                candidates.append(candidate_json)
                conjecture_counter += 1
                
                if len(candidates) >= max_results:
                    break
                    
        return candidates