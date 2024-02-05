import copy

import pytest


from .poset import Poset, PosetAsymmetryException


class TestPoset:
    def test_predecessor_and_successor(self):
        poset = Poset({"A", "B", "C", "D", "E"})
        poset.link("A", "B")
        poset.link("C", "D")
        poset.link("D", "B")
        poset.link("D", "E")
        assert poset.predecessors("A") == set()
        assert poset.predecessors("B") == {"A", "D", "C"}
        assert poset.predecessors("C") == set()
        assert poset.predecessors("D") == {"C"}
        assert poset.predecessors("E") == {"D", "C"}

        assert poset.successors("A") == {"B"}
        assert poset.successors("B") == set()
        assert poset.successors("C") == {"D", "B", "E"}
        assert poset.successors("D") == {"B", "E"}
        assert poset.successors("E") == set()

    def test_order(self):
        poset = Poset({"a1", "b1", "b2", "b3"})
        poset.order("a1", "b2")
        poset.order("b1", "b2")
        poset.order("b2", "b3")
        assert poset.check("a1", "b3")
        assert poset.check("b1", "b3")

    def test_order_cycle_1(self):
        poset = Poset({"A", "B"})
        assert poset.order("A", "B")
        assert not poset.order("B", "A")

    def test_order_cycle_2(self):
        poset = Poset({"A", "B", "C"})
        assert poset.order("A", "B")
        assert poset.order("B", "C")
        assert not poset.order("C", "A")

    def test_copy(self):
        poset = Poset({"A", "B", "C"})
        poset.order("A", "B")
        c = copy.deepcopy(poset)
        poset.order("B", "C")
        assert poset.check("A", "C") == True
        assert c.check("A", "C") == False

    def test_refinements(self):
        # TODO: need better testing
        poset = Poset({"a1", "b1", "b2", "b3"})
        poset.order("b1", "b2")
        poset.order("b2", "b3")
        ref = poset.refinements()
        assert len(ref) == 10

    def test_all_topological_sort(self):
        poset = Poset({"a1", "b1", "b2", "b3"})
        poset.order("b1", "b2")
        poset.order("b2", "b3")
        t1 = poset.all_topological_sorts()
        assert len([*t1]) == 4

        poset.order("a1", "b2")
        t2 = poset.all_topological_sorts()
        assert len([*t2]) == 2
