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

        self.process_last_op = dict[str, str]()
        for process, ops in data.items():
            self.process_last_op[process] = f"{process}.{ops[-1]}"

        self.hb: dict[list[tuple[str, str]]] = self.make_hb()

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

    def make_hb(self) -> dict[list[tuple[str, str]]]:
        hb = dict[list[tuple[str, str]]]()
        for process, _ in self.process_last_op.items():
            hb[process] = []

        for wr, rd in self.write_read_relations.items():
            rd_process = rd[0]
            v = self.label[rd].arg
            rd_ret = self.label[rd].ret

            r_anc = nx.ancestors(self.poset.G, rd)
            for id in r_anc:
                op = self.label[id]
                if op.method == "wr" and op.arg[0] == v and op.arg[1] != rd_ret:
                    hb[rd_process].append((id, wr))

        return hb

    def is_write_co_init_read(self) -> bool:
        """
        This method has to be preceded by self.make_co
        :returns True if WriteCoInitRead
        """
        rd_init: list(tuple[str, Operation]) = []  # (id, Operation)
        for id, op in self.label.items():
            if op.method == "rd" and op.ret is None:
                rd_init.append((id, op))

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

    def is_write_hb_init_read(self) -> bool:
        init_rds = list[Operation]()
        for id, op in self.label.items():
            if op.method == "rd" and not op.ret:
                init_rds.append(op)

        for op in init_rds:
            process = op.op_id[0]
            cp = deepcopy(self.poset)
            for s, d in self.hb[process]:
                cp.link(s, d)

            anc_rd = nx.ancestors(cp.G, op.op_id)
            for id in anc_rd:
                op1 = self.label[id]
                if op1.method == "wr" and op1.arg[0] == op.arg:
                    return True

        return False

    def is_cyclic_hb(self) -> bool:
        for _, hbo in self.hb.items():
            cp = deepcopy(self.poset)
            for tup in hbo:
                cp.link(tup[0], tup[1])
            if not nx.is_directed_acyclic_graph(cp.G):
                return True

        return False


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


class CMBPResult(NamedTuple):
    is_CM: bool
    bad_pattern: BadPattern


def find_cm_bad_pattern(h: WRMemoryHistory) -> CMBPResult:
    if h.bp:
        return CMBPResult(False, h.bp)
    if h.is_write_co_init_read():
        return CMBPResult(False, BadPattern.WriteCOInitRead)
    if h.is_write_co_read():
        return CMBPResult(False, BadPattern.WriteCORead)
    if h.is_write_hb_init_read():
        return CMBPResult(False, BadPattern.WriteHBInitRead)
    if h.is_cyclic_hb():
        return CMBPResult(False, BadPattern.CyclicHB)
    return CMBPResult(True, None)
