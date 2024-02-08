import logging
from abc import ABC, abstractmethod
from copy import deepcopy
from types import MappingProxyType
from typing import Any, NamedTuple

from c3py.poset import Poset

logger = logging.getLogger(__name__)


class Instruction(NamedTuple):
    method: Any
    arg: Any


class Operation(NamedTuple):
    method: Any
    arg: Any
    ret: Any = None

    def to_instruction(self):
        return Instruction(self.method, self.arg)


class History:
    def __init__(self, data):
        # validation
        assert isinstance(data, dict), "data should be a dictionary"
        for _, ops in data.items():
            for op in ops:
                assert isinstance(op, Operation), "invalid operation"

        self.operations = set()
        self.label = dict[str, Operation]()
        for process, ops in data.items():
            for i in range(len(ops)):
                op_id = f"{process}.{i + 1}"
                self.operations.add(op_id)
                self.label[op_id] = ops[i]

        self.poset = Poset(self.operations)
        for process, ops in data.items():
            for i in range(len(ops) - 1):
                self.poset.order_try(f"{process}.{i + 1}", f"{process}.{i + 2}")

    def causal_hist(self, op_id: str, ret_set: set[str]):
        ch = deepcopy(self)
        p = ch.poset.predecessors(op_id)
        p.add(op_id)
        ch.operations = p
        ch.poset = ch.poset.subset(p)
        ch.label = {
            op_id: op if op_id in ret_set else op.to_instruction()
            for op_id, op in ch.label.items()
        }
        return ch

    def causal_arb(self, op_id: str, arb: list[str]) -> list[Instruction | Operation]:
        """compute CausalArb(op_id){op_id} for `arb`

        Because `arb` is a strict total order, this function returns a history as a list of `Instruction`s and `Operation`s.
        """
        p = self.poset.predecessors(op_id)
        p.add(op_id)
        # filter out operations that are not in the causal history
        arb = [o for o in arb if o in p]
        idx = arb.index(op_id)
        history: list[Instruction | Operation] = [
            self.label[o].to_instruction() for o in arb[: (idx + 1)]
        ]
        history[idx] = self.label[op_id]
        return history


class Specification(ABC):
    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def step(self, state, instr: Instruction):
        pass

    def satisfies(self, log):
        state = self.start()
        for instr in log:
            state, op = self.step(state, instr)
            if isinstance(instr, Operation) and op != instr:
                return False
        return True


class RWMemorySpecification(Specification):
    def start(self):
        return MappingProxyType({})

    def step(
        self, state: MappingProxyType, instr: Instruction
    ) -> (MappingProxyType, Operation):
        match instr.method:
            case "wr":
                (key, value) = instr.arg
                return (
                    MappingProxyType(state | {key: value}),
                    Operation("wr", instr.arg, None),
                )
            case "rd":
                key = instr.arg
                return (state, Operation("rd", instr.arg, state.get(key)))
            case _:
                assert False, f"Unexpected method {instr.method}"


# NOTE: `check_CC` and `check_CM` share the common basic structure, but not sure if it makes sense to merge the two functions


def check_CC(h: History, spec: Specification) -> bool:
    for i, co in enumerate(h.poset.refinements()):
        logger.debug(f"check co #{i}: {co}")
        all_op_satisfied = True
        for op_id in co.elements():
            logger.debug(f"    focus on {op_id}: {h.label[op_id]}")
            exists_valid_topological_sort = False

            # TODO: This deepcopy is probably not necessary (the same for other functions)
            ch = deepcopy(h)
            ch.poset = co
            ch = ch.causal_hist(op_id, {op_id})
            ros = [*ch.poset.all_topological_sorts()]
            logger.debug(f"    {len(ros)} possible topological orderings")

            for ro in ros:
                log = [ch.label[op_id] for op_id in ro]
                logger.debug(f"        checking: {log}")
                if spec.satisfies(log):
                    logger.debug("        satisfied")
                    logger.info(f"        found satisfying serialization: {ro}")
                    exists_valid_topological_sort = True
                    break
                else:
                    logger.debug("        not satisfied")

            if not exists_valid_topological_sort:
                all_op_satisfied = False
                break
        if all_op_satisfied:
            return True
    return False


def check_CM(h: History, spec: Specification) -> bool:
    for i, co in enumerate(h.poset.refinements()):
        logger.debug(f"check co #{i}: {co}")
        all_op_satisfied = True
        for op_id in co.elements():
            logger.debug(f"    focus on {op_id}: {h.label[op_id]}")
            exists_valid_topological_sort = False

            ch = deepcopy(h)
            ch.poset = co
            p = ch.poset.predecessors(op_id)
            p.add(op_id)
            ch = ch.causal_hist(op_id, p)
            ros = [*ch.poset.all_topological_sorts()]
            logger.debug(f"    {len(ros)} possible topological orderings")

            for ro in ros:
                log = [ch.label[op_id] for op_id in ro]
                logger.debug(f"        checking: {log}")
                if spec.satisfies(log):
                    logger.debug("        satisfied")
                    exists_valid_topological_sort = True
                    break
                else:
                    logger.debug("        not satisfied")

            if not exists_valid_topological_sort:
                all_op_satisfied = False
                break
        if all_op_satisfied:
            return True
    return False


def check_CV(h: History, spec: Specification) -> bool:
    for i, co in enumerate(h.poset.refinements()):
        logger.debug(f"check co #{i}: {co}")
        arbs = co.all_topological_sorts()
        for j, arb in enumerate(arbs):
            logger.debug(f"    check arb #{j}: {arb}")
            all_op_satisfied = True
            for op_id in co.elements():
                logger.debug(f"        focus on {op_id}")
                ch = deepcopy(h)
                ch.poset = co
                log = ch.causal_arb(op_id, arb)
                logger.debug(f"        log: {log}")
                if not spec.satisfies(log):
                    logger.debug("        not satisfied")
                    all_op_satisfied = False
                    break
                else:
                    logger.debug("        satisfied")
            if all_op_satisfied:
                return True
    return False
