from collections import deque
from copy import deepcopy
from itertools import permutations, product
from typing import Any

import networkx as nx
import pydot


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
        # for our purposes, we only care about the set of edges
        return hash(frozenset(self.G.edges))

    def link(self, a: str, b: str):
        self.G.add_edge(a, b)

    def predecessors(self, node: str) -> set[str]:
        """
        Returns a set of all predecessors of the given node in the poset.

        Parameters:
            node (str): The node for which to find predecessors.

        Returns:
            set[str]: A set of all predecessors of the given node. The set will contain the node itself.
        """
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
        return predecessors

    def successors(self, node: str) -> set[str]:
        """
        Returns the set of successors of the given node in the poset.

        Parameters:
        - node (str): The node for which to find the successors.

        Returns:
        - set[str]: The set of successors of the given node. The set will contain the node itself.
        """
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
        s = self.successors(b)
        if len(p.intersection(s)) > 0:
            self.asymmetry_violation_cache.add((a, b))
            return False
        return True

    def order_force(self, a: str, b: str):
        p = self.predecessors(a)
        s = self.successors(b)
        for src, dst in product(p, s):
            self.link(src, dst)

    def order_try(self, a: str, b: str):
        if self.can_order(a, b):
            self.order_force(a, b)
            return True
        return False

    def check(self, a: str, b: str):
        return self.G.has_edge(a, b)

    def refinements(self) -> set["Poset"]:
        elements = set(self.G.nodes)
        pairs = set(permutations(elements, 2))
        existing_pairs = {e for e in self.G.edges}
        reverse_existing_pairs = {(b, a) for a, b in existing_pairs}
        pairs = list(pairs - existing_pairs - reverse_existing_pairs)
        pair_count = len(pairs)  # number of pairs
        r = set()  # refinements
        q = deque([(self, 0)])
        while len(q) > 0:
            poset, n = q.popleft()
            r.add(deepcopy(poset))

            # base case
            if n == pair_count:
                continue

            # don't add edge
            q.append((poset, n + 1))

            # add edge
            u, v = pairs[n]
            if poset.check(u, v):
                # already connected
                continue
            if not poset.can_order(u, v):
                # would break asymmetry
                continue
            poset = deepcopy(poset)
            poset.order_force(u, v)
            q.append((poset, n + 1))
        return r

    def all_topological_sorts(self):
        return nx.all_topological_sorts(self.G)

    def visualize(self, mapping: Any) -> pydot.Dot:
        TR = nx.transitive_reduction(self.G)
        if mapping is not None:
            TR = nx.relabel_nodes(TR, mapping)
        return nx.nx_pydot.to_pydot(TR)
