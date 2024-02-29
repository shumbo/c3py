from copy import deepcopy
from enum import Enum
from typing import Any, Self

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
    def check_differentiated_h(self) -> bool:
        wr = set[Operation.arg]()
        for id, op in self.label.items():
            if op.method == "wr":
                if op.arg in wr:
                    return False
                wr.add(op.arg)
        return True

    def make_co(self) -> Self | BadPattern:
        """
        co = (po U wr)^+
        po is checked in History.__init__
        so just check wr here
        """
        wr = dict[tuple[Any, Any], str]()
        for id, op in self.label.items():
            if op.method == "wr":
                wr[op.arg] = id

        ch = deepcopy(self)
        for id, op in self.label.items():
            if op.method == "rd":
                src = wr.get((op.arg, op.ret))
                if not src:
                    continue
                ch.poset.link(src, id)

        if not nx.is_directed_acyclic_graph(ch.poset.G):
            return BadPattern.CyclicCO

        # ensure transitivity of poset
        tc = nx.transitive_closure(ch.poset.G, reflexive=False)
        missing_es = tc.edges() - ch.poset.G.edges()
        for e in missing_es:
            ch.poset.link(e[0], e[1])

        return ch

    def is_write_co_init_read(self) -> bool:
        """
        This method has to be preceded by self.make_co
        :returns True if WriteCoInitRead
        """
        rd_init: list(tuple[str, Operation]) = []   # (id, Operation)
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

    def is_thin_air_read(self) -> bool:
        wrs: list[Operation.arg] = []
        rds = set[(Operation.arg, Operation.ret)]()
        for _, op in self.label.items():
            if op.method == "wr":
                wrs.append(op.arg)
            else:
                rds.add((op.arg, op.ret))

        for wr in wrs:
            rds.remove(wr)

        return rds != set()

    def is_write_co_read(self) -> bool:
        # ToDo do this in make_co
        wr = dict[tuple[Any, Any], str]()
        for id, op in self.label.items():
            if op.method == "wr":
                wr[op.arg] = id

        wr_relations = list[tuple[str, str, str]]()  # [(var, wr1, rd1), (var, wr2, rd2), ...]
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
