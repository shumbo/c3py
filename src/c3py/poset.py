from copy import deepcopy
from itertools import permutations, product

import networkx as nx


class PosetAsymmetryException(Exception):
    pass


class Poset:
    def __init__(self, elements):
        self.G = nx.DiGraph()
        self.G.add_nodes_from(elements)

        self.asymmetry_violation_cache = set()

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, Poset):
            return nx.utils.graphs_equal(self.G, __value.G)
        return self == __value

    def __hash__(self) -> int:
        return hash(nx.weisfeiler_lehman_graph_hash(self.G))

    def link(self, a: str, b: str):
        self.G.add_edge(a, b)

    def predecessors(self, node: str) -> set[str]:
        p = set(nx.single_source_shortest_path_length(self.G.reverse(), node).keys())
        p.remove(node)
        return p

    def successors(self, node: str) -> set[str]:
        s = set(nx.single_source_shortest_path_length(self.G, node).keys())
        s.remove(node)
        return s

    def elements(self) -> set[str]:
        return set(self.G.nodes)

    def subset(self, nodes):
        s = deepcopy(self)
        s.G = s.G.subgraph(nodes)
        s.asymmetry_violation_cache = set()
        return s

    def order(self, a: str, b: str):
        if (a, b) in self.asymmetry_violation_cache:
            raise PosetAsymmetryException(f"ordering {a} < {b} would violate asymmetry")
        p = self.predecessors(a)
        p.add(a)
        s = self.successors(b)
        s.add(b)
        if len(p.intersection(s)) > 0:
            self.asymmetry_violation_cache.add((a, b))
            raise PosetAsymmetryException(f"ordering {a} < {b} would violate asymmetry")
        for src, dst in product(p, s):
            self.link(src, dst)

    def check(self, a: str, b: str):
        return self.G.has_edge(a, b)

    def refinements(self) -> set["Poset"]:
        # print(f"refine d={depth}")
        elements = set(self.G.nodes)
        refinements = set()
        for src, dst in permutations(elements, 2):
            if self.check(src, dst):
                # already ordered
                continue
            poset = deepcopy(self)
            try:
                # try ordering these two elements
                poset.order(src, dst)
            except PosetAsymmetryException:
                continue
            # if src < dst is possible
            refinements.add(poset)
            refinements.update(poset.refinements())
        return refinements

    def all_topological_sorts(self):
        return nx.all_topological_sorts(self.G)

    def visualize(self):
        return nx.nx_pydot.to_pydot(self.G)


if __name__ == "__main__":
    poset = Poset({"a1", "b1", "b2", "b3"})
    poset.order("b1", "b2")
    poset.order("b2", "b3")
    poset.order("a1", "b2")
    poset.visualize().write_png("poset.png")
