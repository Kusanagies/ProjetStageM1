import networkx as nx
import random
import time
import math

class GraphInvariants:
    """Module pour calculer les invariants d'un graphe."""
    @staticmethod
    def calculate_all(G):
        if len(G) == 0:
            return {}
            
        n = G.number_of_nodes()
        m = G.number_of_edges()
        degrees = dict(G.degree()).values()
        
        # Invariants de base
        invariants = {
            "n": n,
            "m": m,
            "density": nx.density(G),
            "delta": min(degrees) if n > 0 else 0, # Degré minimum
            "Delta": max(degrees) if n > 0 else 0, # Degré maximum
            "avg": (2 * m / n) if n > 0 else 0     # Degré moyen
        }
        
        # Invariants métriques (nécessitent un graphe connexe)
        if nx.is_connected(G):
            invariants["rad"] = nx.radius(G)
            invariants["diam"] = nx.diameter(G)
        else:
            invariants["rad"] = float('inf')
            invariants["diam"] = float('inf')
            
        return invariants

class ConjectureEvaluator:
    """Évalue si un graphe viole une conjecture via une fonction de score."""
    def __init__(self, conjecture):
        self.conjecture = conjecture

    def check_graph_class(self, G):
        """Vérifie si le graphe appartient à la classe imposée par la conjecture."""
        if len(G) == 0:
            return False
            
        g_class = self.conjecture.get("graph_class", "connected")
        if g_class == "connected":
            return nx.is_connected(G)
        elif g_class == "tree":
            return nx.is_tree(G)
        elif g_class == "planar":
            return nx.check_planarity(G)[0]
        elif g_class == "bipartite":
            return nx.is_bipartite(G)
        return True

    def evaluate_expression(self, expr, invariants):
        """Évalue l'expression mathématique de droite avec les invariants du graphe."""
        # On remplace les notations mathématiques classiques pour Python
        expr = expr.replace("^", "**")
        try:
            # Évaluation sécurisée des mathématiques
            return eval(expr, {"__builtins__": None, "math": math}, invariants)
        except Exception as e:
            return float('inf')

    def calculate_score(self, G):
        """
        Calcule le score de violation. 
        Un score < 0 signifie que la conjecture est invalidée (contre-exemple trouvé).
        """
        if not self.check_graph_class(G):
            return 1000.0 # Forte pénalité si le graphe sort de la classe
            
        invs = GraphInvariants.calculate_all(G)
        
        # Récupération des éléments de l'inégalité
        ineq = self.conjecture["inequality"]
        left_invariant = ineq["left_invariant"]
        right_expr = ineq["right_expression"]
        relation = ineq["relation"]
        
        left_val = invs.get(left_invariant, float('inf'))
        right_val = self.evaluate_expression(right_expr, invs)
        
        if left_val == float('inf') or right_val == float('inf'):
            return 1000.0
            
        # Transformation en fonction de score à minimiser
        if relation == "<=":
            # Conjecture: Y <= f(X). Violation si Y > f(X). Score = f(X) - Y
            return right_val - left_val
        elif relation == ">=":
            # Conjecture: Y >= f(X). Violation si Y < f(X). Score = Y - f(X)
            return left_val - right_val
            
        return float('inf')

class GraphMutator:
    """Génère un voisinage pour la recherche locale (mutations)."""
    @staticmethod
    def mutate(G):
        G_new = G.copy()
        n = G_new.number_of_nodes()
        
        # Liste des mutations élémentaires possibles
        mutations = ["add_edge", "remove_edge", "add_node", "remove_node"]
        
        # Sécurité : on ne retire pas de sommet si le graphe est trop petit
        if n <= 3:
            mutations.remove("remove_node")
            if G_new.number_of_edges() == 0:
                mutations.remove("remove_edge")
                
        choice = random.choice(mutations)
        
        if choice == "add_node":
            G_new.add_node(n)
            # Pour éviter les graphes déconnectés, on le relie à un sommet existant
            if n > 0:
                G_new.add_edge(n, random.choice(list(G_new.nodes())[:-1]))
                
        elif choice == "remove_node":
            node_to_remove = random.choice(list(G_new.nodes()))
            G_new.remove_node(node_to_remove)
            # Re-labelliser pour garder des entiers propres
            G_new = nx.convert_node_labels_to_integers(G_new)
            
        elif choice == "add_edge":
            u, v = random.sample(list(G_new.nodes()), 2)
            G_new.add_edge(u, v)
            
        elif choice == "remove_edge":
            edges = list(G_new.edges())
            if edges:
                u, v = random.choice(edges)
                G_new.remove_edge(u, v)
                
        return G_new

class Invalidator:
    """Le moteur de recherche locale (Hill Climbing)."""
    def __init__(self, evaluator):
        self.evaluator = evaluator

    def search(self, max_iterations=5000, timeout_seconds=120):
        start_time = time.time()
        
        # 1. Graphe initial : un petit chemin
        current_graph = nx.path_graph(4)
        current_score = self.evaluator.calculate_score(current_graph)
        
        for iteration in range(max_iterations):
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout_seconds:
                return {
                    "status": "no_counterexample_found",
                    "reason": "timeout",
                    "time_seconds": round(elapsed_time, 2),
                    "best_score": current_score
                }
                
            # 2. Critère d'arrêt : on a trouvé une violation !
            if current_score < 0:
                g6_value = nx.to_graph6_bytes(current_graph).decode('ascii').strip()
                return {
                    "status": "counterexample_found",
                    "format": "graph6",
                    "value": g6_value,
                    "score": round(current_score, 4),
                    "iterations": iteration,
                    "time_seconds": round(elapsed_time, 2)
                }
            
            # 3. Explorer le voisinage
            candidate_graph = GraphMutator.mutate(current_graph)
            candidate_score = self.evaluator.calculate_score(candidate_graph)
            
            # 4. Hill Climbing : on accepte si le score est meilleur ou égal (pour naviguer sur les plateaux)
            if candidate_score <= current_score:
                current_graph = candidate_graph
                current_score = candidate_score
                
        return {
            "status": "no_counterexample_found",
            "reason": "max_iterations_reached",
            "time_seconds": round(time.time() - start_time, 2),
            "best_score": current_score
        }

# ==========================================
# TEST D'EXÉCUTION (Conjecture HDR-001)
# ==========================================
if __name__ == "__main__":
    # Format JSON issu de la tâche 2
    conjecture_hdr_001 = {
        "id": "HDR-001",
        "graph_class": "connected",
        "inequality": {
            "left_invariant": "density",
            "relation": "<=",
            "right_expression": "65/98 + (18/29)*rad - (17/53)*rad^2 + (1/28)*rad^3"
        }
    }

    print(f"Lancement de la recherche pour la conjecture {conjecture_hdr_001['id']}...")
    
    evaluator = ConjectureEvaluator(conjecture_hdr_001)
    search_engine = Invalidator(evaluator)
    
    # On lance la recherche
    result = search_engine.search(max_iterations=10000, timeout_seconds=30)
    
    print("\nRésultat de la recherche :")
    import json
    print(json.dumps(result, indent=4))