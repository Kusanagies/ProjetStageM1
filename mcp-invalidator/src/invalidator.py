import networkx as nx
import random
import time
import math
from collections import OrderedDict

class GraphInvariants:
    @staticmethod
    def calculate_all(G):
        if len(G) == 0:
            return {}
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
        else:
            invs["rad"] = float('inf')
            invs["diam"] = float('inf')
        return invs

class ConjectureEvaluator:
    def __init__(self, conjecture):
        self.conjecture = conjecture

    def check_graph_class(self, G):
        if len(G) == 0: return False
        g_class = self.conjecture.get("graph_class", "connected")
        if g_class == "connected": return nx.is_connected(G)
        elif g_class == "tree": return nx.is_tree(G)
        elif g_class == "planar": return nx.check_planarity(G)[0]
        elif g_class == "bipartite": return nx.is_bipartite(G)
        return True

    def calculate_score(self, G):
        if not self.check_graph_class(G):
            return float('inf') # Pénalité stricte si la classe n'est pas respectée
            
        invs = GraphInvariants.calculate_all(G)
        ineq = self.conjecture["inequality"]
        left_invariant = ineq["left_invariant"]
        right_expr = ineq["right_expression"].replace("^", "**")
        relation = ineq["relation"]
        
        left_val = invs.get(left_invariant, float('inf'))
        try:
            right_val = eval(right_expr, {"__builtins__": None, "math": math}, invs)
        except Exception:
            return float('inf')
            
        if relation == "<=": return right_val - left_val
        elif relation == ">=": return left_val - right_val
        return float('inf')

class GraphScoreCache:
    
    def __init__(self, max_size=5000):
        self._data = OrderedDict()
        self._limit = max_size

    def get(self, key):
        if key in self._data:
            self._data.move_to_end(key)
            return self._data[key]
        return None

    def set(self, key, score):
        self._data[key] = score
        self._data.move_to_end(key)
        if len(self._data) > self._limit:
            self._data.popitem(last=False)

class GraphMutator:
    @staticmethod
    def mutate(G, max_mutations=2):
        
        mutated = G.copy()
        
        mutations_funcs = [
            GraphMutator._mutation_add_edge,
            GraphMutator._mutation_remove_edge,
            GraphMutator._mutation_add_vertex,
            GraphMutator._mutation_remove_vertex,
            GraphMutator._mutation_replace_by_star
        ]
        
        for _ in range(random.randint(1, max_mutations)):
            func = random.choice(mutations_funcs)
            mutated = func(mutated)
        return mutated

    @staticmethod
    def _mutation_add_edge(G):
        if G.number_of_nodes() < 2: return G
        u, v = random.sample(list(G.nodes()), 2)
        G.add_edge(u, v)
        return G

    @staticmethod
    def _mutation_remove_edge(G):
        if G.number_of_edges() > 0:
            u, v = random.choice(list(G.edges()))
            G.remove_edge(u, v)
        return G

    @staticmethod
    def _mutation_add_vertex(G):
        n = G.number_of_nodes() if G.nodes else 0
        new_node = max(G.nodes()) + 1 if n > 0 else 0
        G.add_node(new_node)
        if n > 0:
            G.add_edge(new_node, random.choice(list(G.nodes())[:-1]))
        return G

    @staticmethod
    def _mutation_remove_vertex(G):
        if G.number_of_nodes() > 3:
            G.remove_node(random.choice(list(G.nodes())))
            G = nx.convert_node_labels_to_integers(G)
        return G

    @staticmethod
    def _mutation_replace_by_star(G):
        
        if G.number_of_nodes() < 3: return G
        v = random.choice(list(G.nodes()))
        neighbors = list(G.neighbors(v))
        G.remove_node(v)
        
        center = G.number_of_nodes()
        G.add_node(center)
        for i in range(1, 4):
            branch = center + i
            G.add_node(branch)
            G.add_edge(center, branch)
            
        for n in neighbors:
            if G.has_node(n): G.add_edge(n, center)
            
        return nx.convert_node_labels_to_integers(G)

    @staticmethod
    def mutate_tree(G, max_mutations=2):
        mutated = G.copy()
        for _ in range(random.randint(1, max_mutations)):
            mutated = GraphMutator._tree_move_leaf(mutated)
        return mutated

    @staticmethod
    def _tree_move_leaf(G):
        leaves = [v for v in G.nodes() if G.degree(v) == 1]
        if not leaves or G.number_of_nodes() < 3:
            return G
        leaf = random.choice(leaves)
        parent = list(G.neighbors(leaf))[0]
        candidates = [v for v in G.nodes() if v != leaf and v != parent]
        if not candidates:
            return G
        G.remove_edge(leaf, parent)
        G.add_edge(leaf, random.choice(candidates))
        return G

    @staticmethod
    def mutate_planar(G, max_mutations=2):
        mutated = G.copy()
        for _ in range(random.randint(1, max_mutations)):
            func = random.choice([
                GraphMutator._planar_add_edge,
                GraphMutator._mutation_remove_edge,
                GraphMutator._mutation_add_vertex,
                GraphMutator._mutation_remove_vertex,
            ])
            mutated = func(mutated)
        return mutated

    @staticmethod
    def _planar_add_edge(G):
        if G.number_of_nodes() < 2:
            return G
        nodes = list(G.nodes())
        random.shuffle(nodes)
        for u in nodes:
            for v in nodes:
                if u != v and not G.has_edge(u, v):
                    G.add_edge(u, v)
                    if nx.check_planarity(G)[0]:
                        return G
                    G.remove_edge(u, v)
        return G

    @staticmethod
    def mutate_bipartite(G, max_mutations=2):
        mutated = G.copy()
        for _ in range(random.randint(1, max_mutations)):
            func = random.choice([
                GraphMutator._bipartite_add_edge,
                GraphMutator._mutation_remove_edge,
                GraphMutator._bipartite_add_vertex,
                GraphMutator._mutation_remove_vertex,
            ])
            mutated = func(mutated)
        return mutated

    @staticmethod
    def _bipartite_add_edge(G):
        if not nx.is_bipartite(G) or G.number_of_nodes() < 2:
            return G
        top, bottom = nx.bipartite.sets(G)
        top, bottom = list(top), list(bottom)
        if not top or not bottom:
            return G
        G.add_edge(random.choice(top), random.choice(bottom))
        return G

    @staticmethod
    def _bipartite_add_vertex(G):
        if not nx.is_bipartite(G) or G.number_of_nodes() < 2:
            return G
        top, bottom = nx.bipartite.sets(G)
        top, bottom = list(top), list(bottom)
        new_node = max(G.nodes()) + 1
        if len(top) <= len(bottom):
            G.add_node(new_node)
            if bottom:
                G.add_edge(new_node, random.choice(bottom))
        else:
            G.add_node(new_node)
            if top:
                G.add_edge(new_node, random.choice(top))
        return G

class Invalidator:
    def __init__(self, evaluator):
        self.evaluator = evaluator
        self.cache = GraphScoreCache(max_size=5000)

    def _get_mutator_and_start(self):
        g_class = self.evaluator.conjecture.get("graph_class", "connected")
        if g_class == "tree":
            return GraphMutator.mutate_tree, nx.random_labeled_tree(6)
        elif g_class == "planar":
            return GraphMutator.mutate_planar, nx.path_graph(5)
        elif g_class == "bipartite":
            return GraphMutator.mutate_bipartite, nx.complete_bipartite_graph(3, 3)
        else:
            return GraphMutator.mutate, nx.path_graph(5)

    def _random_restart(self):
        g_class = self.evaluator.conjecture.get("graph_class", "connected")
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

    def search(self, max_iterations=5000, timeout_seconds=120, neighbor_count=15, stagnation_limit=20):
        start_time = time.time()
        
        mutate_fn, current_graph = self._get_mutator_and_start()
        current_key = nx.to_graph6_bytes(current_graph, header=False).decode("ascii").strip()
        current_score = self.evaluator.calculate_score(current_graph)
        self.cache.set(current_key, current_score)
        
        best_score = current_score
        no_improve_counter = 0
        resets = 0

        for iteration in range(max_iterations):
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                return {"status": "no_counterexample_found", "reason": "timeout", "time_seconds": round(elapsed, 2), "best_score": best_score}
                
            if current_score < 0:
                g6_val = nx.to_graph6_bytes(current_graph, header=False).decode("ascii").strip()
                return {"status": "counterexample_found", "format": "graph6", "value": g6_val, "score": current_score, "iterations": iteration, "time_seconds": round(elapsed, 2)}
                
            neighbors = []
            for _ in range(neighbor_count): 
                candidate_graph = mutate_fn(current_graph, max_mutations=3)
                candidate_key = nx.to_graph6_bytes(candidate_graph).decode("ascii").strip()
                
                cached_score = self.cache.get(candidate_key)
                if cached_score is not None:
                    candidate_score = cached_score
                else:
                    candidate_score = self.evaluator.calculate_score(candidate_graph)
                    self.cache.set(candidate_key, candidate_score)
                
                if candidate_score != float('inf'):
                    neighbors.append((candidate_graph, candidate_score))
            
            if not neighbors:
                no_improve_counter += 1
                continue
                
            best_neighbor, best_neighbor_score = min(neighbors, key=lambda x: x[1])
            
            if best_neighbor_score <= current_score:
                current_graph = best_neighbor
                current_score = best_neighbor_score
                if best_neighbor_score < best_score:
                    best_score = best_neighbor_score
                    no_improve_counter = 0
                else:
                    no_improve_counter += 1
            else:
                no_improve_counter += 1
                
            if no_improve_counter >= stagnation_limit:
                resets += 1
                current_graph = self._random_restart()
                current_score = self.evaluator.calculate_score(current_graph)
                no_improve_counter = 0

        return {"status": "no_counterexample_found", "reason": "max_iterations_reached", "time_seconds": round(time.time() - start_time, 2), "best_score": best_score}
