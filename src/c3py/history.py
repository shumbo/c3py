from copy import deepcopy
from typing import Any, NamedTuple
from abc import ABC, abstractmethod
from types import MappingProxyType

from .poset import Poset


class Instruction(NamedTuple):
    method: Any
    arg: Any


class Operation(NamedTuple):
    method: Any
    arg: Any
    ret: Any

    def to_instruction(self):
        return Instruction(self.method, self.arg)


class History:
    def __init__(self, data):
        # validation
        assert type(data) == dict, "data should be a dictionary"
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
                self.poset.order(f"{process}.{i + 1}", f"{process}.{i + 2}")

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


def check_CC(h: History, spec: Specification) -> bool:
    # a history is valid if there exists a co that refines program order
    # for co in h.poset.refinements():
    #     print("check co")
    #     is_valid_co = True
    #     # for all operation
    #     for op_id in co.elements():
    #         print(f"for operation {op_id}")
    #         ch = h.causal_hist(op_id, {op_id})
    #         ros = ch.poset.all_topological_sorts()
    #         found_satisfying_order = False
    #         for ro in ros:
    #             log = [ch.label[op_id] for op_id in ro]
    #             if spec.satisfies(log):
    #                 found_satisfying_order = True
    #                 break
    #         if found_satisfying_order:
    #             break
    #     if is_valid_co:
    #         return True
    # return False

    for i, co in enumerate(h.poset.refinements()):
        print(f"check co #{i}", co)
        # co.visualize().write_png(f"viz/{i}.png")
        all_op_satisfied = True
        for op_id in co.elements():
            print(f"    focus on {op_id}: ", h.label[op_id])
            exists_valid_topological_sort = False

            ch = deepcopy(h)
            ch.poset = co
            ch = ch.causal_hist(op_id, {op_id})
            ros = [*ch.poset.all_topological_sorts()]
            print(f"    {len(ros)} possible topological orderings")

            for ro in ros:
                log = [ch.label[op_id] for op_id in ro]
                print("        checking:", log)
                if spec.satisfies(log):
                    print("        satisfied")
                    exists_valid_topological_sort = True
                    break
                else:
                    print("        not satisfied")

            if not exists_valid_topological_sort:
                all_op_satisfied = False
                break
        if all_op_satisfied:
            return True
    return False


if __name__ == "__main__":
    h = History(
        {
            "a": [Operation("wr", ("x", 1), None), Operation("wr", ("y", 1), None)],
            "b": [Operation("rd", "y", 1), Operation("wr", ("x", 2), None)],
            "c": [
                Operation("rd", "x", 2),
                # Operation("rd", "x", 1),
            ],
        }
    )
    print(check_CC(h, RWMemorySpecification()))
    # print(h.program_order.visualize().write_png("po.png"))
