import networkx as nx
import math

class IndependentVerifier:
    """
    Module indépendant de vérification mathématique (Tâche 4).
    Prend en entrée la définition de la conjecture et la chaîne g6 d'un graphe.
    """
    
    @staticmethod
    def verify(conjecture: dict, g6_value: str) -> dict:
        """
        Vérifie indépendamment si le graphe g6 est un contre-exemple valide.
        """
        # 1. RECONSTRUCTION INDÉPENDANTE DU GRAPHE
        try:
            # nx.from_graph6_bytes nécessite des bytes en entrée
            G = nx.from_graph6_bytes(g6_value.encode('ascii'))
        except Exception as e:
            return {
                "hypotheses_satisfied": False,
                "conclusion_satisfied": False,
                "error": f"Format g6 invalide : {str(e)}"
            }

        # 2. VÉRIFICATION DES HYPOTHÈSES (Classe du graphe)
        hypotheses_satisfied = IndependentVerifier._check_hypotheses(G, conjecture.get("graph_class", "connected"))

        # 3. VÉRIFICATION DE LA CONCLUSION (L'inégalité est-elle respectée ?)
        conclusion_satisfied = IndependentVerifier._check_conclusion(G, conjecture.get("inequality", {}))

        return {
            "hypotheses_satisfied": hypotheses_satisfied,
            "conclusion_satisfied": conclusion_satisfied,
            # C'est un contre-exemple valide SI ET SEULEMENT SI :
            "is_valid_counterexample": hypotheses_satisfied and (not conclusion_satisfied)
        }

    @staticmethod
    def _check_hypotheses(G, graph_class: str) -> bool:
        """Vérifie le point 1 : Le graphe satisfait les hypothèses de la conjecture."""
        if G.number_of_nodes() == 0:
            return False
            
        if graph_class == "connected":
            return nx.is_connected(G)
        elif graph_class == "tree":
            return nx.is_tree(G)
        elif graph_class == "planar":
            return nx.check_planarity(G)[0]
        elif graph_class == "bipartite":
            return nx.is_bipartite(G)
        # Vous pourrez rajouter "claw free" plus tard si besoin
        return True

    @staticmethod
    def _check_conclusion(G, inequality: dict) -> bool:
        """
        Vérifie le point 2 : L'évaluation froide de la conclusion mathématique.
        Retourne True si la conjecture est VRAIE pour ce graphe, False si elle est VIOLÉE.
        """
        if not inequality:
            return True # Sans inégalité, on ne peut rien réfuter

        # Recalcul indépendant des invariants de base pour ce graphe
        n = G.number_of_nodes()
        m = G.number_of_edges()
        
        invs = {
            "n": n,
            "m": m,
            "density": nx.density(G)
        }
        
        if n > 0:
            degrees = dict(G.degree()).values()
            invs["delta"] = min(degrees)
            invs["Delta"] = max(degrees)
            invs["avg"] = 2 * m / n
            
        if nx.is_connected(G):
            invs["rad"] = nx.radius(G)
            invs["diam"] = nx.diameter(G)
        else:
            invs["rad"] = float('inf')
            invs["diam"] = float('inf')

        # Évaluation des deux côtés de l'inégalité
        left_invariant = inequality["left_invariant"]
        right_expr = inequality["right_expression"].replace("^", "**")
        relation = inequality["relation"]

        left_val = invs.get(left_invariant, float('inf'))
        
        try:
            right_val = eval(right_expr, {"__builtins__": None, "math": math}, invs)
        except Exception:
            return True # En cas d'erreur mathématique, on ne valide pas le contre-exemple

        # On vérifie si l'inégalité est mathématiquement respectée
        if relation == "<=":
            return left_val <= right_val
        elif relation == ">=":
            return left_val >= right_val
        elif relation == "<":
            return left_val < right_val
        elif relation == ">":
            return left_val > right_val
            
        return True