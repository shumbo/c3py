from collections import deque
from copy import deepcopy
from itertools import permutations, product


class PosetAsymmetryException(Exception):
    pass


class Poset:
    def __init__(self, elements: set[str]):
        # a < b if b in self.relation[a]
        self.rel: dict[str, set[str]] = {element: set() for element in elements}
        self.rev_rel: dict[str, set[str]] = {element: set() for element in elements}

        self.asymmetry_violation_cache = set()

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, Poset):
            return self.rel == __value.rel
        return self == __value

    def __hash__(self) -> int:
        return hash(frozenset((k, frozenset(v)) for k, v in self.rel.items()))

    def link(self, a: str, b: str):
        self.rel[a].add(b)
        self.rev_rel[b].add(a)

    def predecessors(self, node: str) -> set[str]:
        predecessors = {*()}
        q = deque([node])
        while len(q) != 0:
            element = q.pop()
            predecessors.add(element)
            for p in self.rev_rel[element]:
                q.append(p)
        # omit node itself
        predecessors.remove(node)
        return predecessors

    def successors(self, node: str) -> set[str]:
        successors = {*()}
        q = deque([node])
        while len(q) != 0:
            element = q.pop()
            successors.add(element)
            for p in self.rel[element]:
                q.append(p)
        successors.remove(node)
        return successors

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
        return b in self.rel[a]

    def refinements(self):
        elements = self.rel.keys()
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

    def visualize(self):
        import graphviz

        dot = graphviz.Digraph()
        for node in self.rel.keys():
            dot.node(node, node)
        for src, dst_set in self.rel.items():
            for dst in dst_set:
                dot.edge(src, dst)
        return dot
