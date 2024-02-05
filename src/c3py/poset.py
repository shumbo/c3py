from collections import deque
from copy import deepcopy
from itertools import chain, combinations, permutations, product

import networkx as nx


def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))


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
        predecessors = {*()}
        added = set()
        q = deque([node])
        while len(q) != 0:
            element = q.pop()
            predecessors.add(element)
            for p in self.G.predecessors(element):
                if p not in added:
                    added.add(p)
                    q.append(p)
        # omit node itself
        predecessors.remove(node)
        return predecessors

    def successors(self, node: str) -> set[str]:
        successors = {*()}
        added = set()
        q = deque([node])
        while len(q) != 0:
            element = q.pop()
            successors.add(element)
            for p in self.G.successors(element):
                if p not in added:
                    added.add(p)
                    q.append(p)
        # omit node itself
        successors.remove(node)
        return successors

    def elements(self) -> set[str]:
        return set(self.G.nodes)

    def subset(self, nodes):
        s = deepcopy(self)
        s.G = s.G.subgraph(nodes)
        s.asymmetry_violation_cache = set()
        return s

    def can_order(self, a: str, b: str):
        if (a, b) in self.asymmetry_violation_cache:
            return False
        p = self.predecessors(a)
        p.add(a)
        s = self.successors(b)
        s.add(b)
        if len(p.intersection(s)) > 0:
            self.asymmetry_violation_cache.add((a, b))
            return False
        return True

    def order_force(self, a: str, b: str):
        p = self.predecessors(a)
        p.add(a)
        s = self.successors(b)
        s.add(b)
        for src, dst in product(p, s):
            self.link(src, dst)

    def order(self, a: str, b: str):
        if (a, b) in self.asymmetry_violation_cache:
            return False
        p = self.predecessors(a)
        p.add(a)
        s = self.successors(b)
        s.add(b)
        if len(p.intersection(s)) > 0:
            self.asymmetry_violation_cache.add((a, b))
            return False
        for src, dst in product(p, s):
            self.link(src, dst)
        return True

    def check(self, a: str, b: str):
        return self.G.has_edge(a, b)

    def refinements(self) -> set["Poset"]:
        # print(f"refine d={depth}")
        elements = set(self.G.nodes)
        pairs = set(permutations(elements, 2))
        existing_pairs = {e for e in self.G.edges}
        pairs = pairs - existing_pairs
        power = powerset(pairs)
        r = set()
        dirty = True
        dc_count = 0
        for edges in power:
            if dirty:
                dc_count += 1
                poset = deepcopy(self)
            for edge in edges:
                u, v = edge
                if poset.check(u, v):
                    # if already connected, is on the gap
                    break
                if not poset.can_order(u, v):
                    break
                poset.order_force(u, v)
                dirty = True
            else:
                # if all edges are added without violating asymmetry, add to the set
                r.add(poset)
        return r

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
