from copy import deepcopy
from enum import Enum
from typing import Any, NamedTuple, Self

import networkx as nx

from c3py.history import History, Operation


class BadPattern(Enum):
    CyclicCO = 1
    WriteCOInitRead = 2
    ThinAirRead = 3
    WriteCORead = 4
    CyclicCF = 5
    WriteHBInitRead = 6
    CyclicHB = 7


class WRMemoryHistory(History):
    def __init__(self, data):
        super().__init__(data)
        assert self.check_differentiated_h()
        self.writes = dict[tuple[Any, Any], str]()
        self.write_read_relations = dict[str, str]()
        self.poset, self.bp = self.make_co()

    def check_differentiated_h(self) -> bool:
        wr = set[Operation.arg]()
        for id, op in self.label.items():
            if op.method == "wr":
                if op.arg in wr:
                    return False
                wr.add(op.arg)
        return True

    def make_co(self) -> tuple[Self, BadPattern]:
        """
        :returns
            tuple[self.poset, BadPattern]

        co = (po U wr)^+
        po is checked in History.__init__
        so just check wr here
        """
        for id, op in self.label.items():
            if op.method == "wr":
                self.writes[op.arg] = id

        cp = deepcopy(self.poset)
        for id, op in self.label.items():
            if op.method == "rd" and op.ret is not None:
                src = self.writes.get((op.arg, op.ret))
                if not src:
                    return cp, BadPattern.ThinAirRead
                cp.link(src, id)
                self.write_read_relations[src] = id

        if not nx.is_directed_acyclic_graph(cp.G):
            return cp, BadPattern.CyclicCO

        # ensure transitivity of poset
        tc = nx.transitive_closure(cp.G, reflexive=False)
        missing_es = tc.edges() - cp.G.edges()
        for e in missing_es:
            cp.link(e[0], e[1])

        return cp, None

    def is_write_co_init_read(self) -> bool:
        """
        This method has to be preceded by self.make_co
        :returns True if WriteCoInitRead
        """
        rd_init: list(tuple[str, Operation]) = []  # (id, Operation)
        for id, op in self.label.items():
            if op.method == "rd" and op.ret is None:
                rd_init.append((id, op))

        if len(rd_init) == 0:
            return False

        for id1, op1 in rd_init:
            anc = nx.ancestors(self.poset.G, id1)
            for id2 in anc:
                op2 = self.label[id2]
                if op2.method == "wr" and op2.arg[0] == op1.arg:
                    return True

        return False

    def is_write_co_read(self) -> bool:
        # ToDo do this in make_co
        wr = dict[tuple[Any, Any], str]()
        for id, op in self.label.items():
            if op.method == "wr":
                wr[op.arg] = id

        wr_relations = list[
            tuple[str, str, str]
        ]()  # [(var, wr1, rd1), (var, wr2, rd2), ...]
        for id, op in self.label.items():
            if op.method == "rd":
                src = wr.get((op.arg, op.ret))
                if not src:
                    continue
                wr_relations.append((op.arg, src, id))

        for v, wr, rd in wr_relations:
            wr_des = nx.descendants(self.poset.G, wr)
            rd_anc = nx.ancestors(self.poset.G, rd)
            intermediates = wr_des.intersection(rd_anc)
            for i in intermediates:
                if self.label[i].method == "wr" and self.label[i].arg[0] == v:
                    return True

        return False

    def is_cyclic_cf(self) -> bool:
        cf = list[tuple[str, str]]()
        for w, r in self.write_read_relations.items():
            v = self.label[r].arg
            r_anc = nx.ancestors(self.poset.G, r)
            for id in r_anc:
                if id == w:
                    continue
                op = self.label[id]
                if op.method == "wr" and op.arg[0] == v:
                    cf.append((id, w))

        cp = deepcopy(self.poset)
        for s, d in cf:
            cp.link(s, d)

        return not nx.is_directed_acyclic_graph(cp.G)


class CCBPResult(NamedTuple):
    is_CC: bool
    bad_pattern: BadPattern


def find_cc_bad_pattern(h: WRMemoryHistory) -> CCBPResult:
    if h.bp:
        return CCBPResult(False, h.bp)
    if h.is_write_co_init_read():
        return CCBPResult(False, BadPattern.WriteCOInitRead)
    if h.is_write_co_read():
        return CCBPResult(False, BadPattern.WriteCORead)
    return CCBPResult(True, None)


class CCvBPResult(NamedTuple):
    is_CCv: bool
    bad_pattern: BadPattern


def find_ccv_bad_pattern(h: WRMemoryHistory) -> CCvBPResult:
    if h.bp:
        return CCvBPResult(False, h.bp)
    if h.is_write_co_init_read():
        return CCvBPResult(False, BadPattern.WriteCOInitRead)
    if h.is_write_co_read():
        return CCvBPResult(False, BadPattern.WriteCORead)
    if h.is_cyclic_cf():
        return CCvBPResult(False, BadPattern.CyclicCF)
    return CCvBPResult(True, None)
