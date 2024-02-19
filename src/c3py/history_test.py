import pytest

from c3py.history import (
    History,
    Instruction,
    Operation,
    RWMemorySpecification,
    check_CC,
    check_CM,
    check_CCv,
)


class TestRWMemorySpecification:
    def test_read_write(self):
        s = RWMemorySpecification()
        st1 = s.start()
        # read key1
        (st2, op1) = s.step(st1, Instruction("rd", "key1"))
        assert op1 == Operation("rd", "key1", None)

        # write key1
        (st3, op2) = s.step(st2, Instruction("wr", ("key1", "hello")))
        assert op2 == Operation("wr", ("key1", "hello"), None)

        # read key1
        (st4, op3) = s.step(st3, Instruction("rd", "key1"))
        assert op3 == Operation("rd", "key1", "hello")

        assert st4 == {"key1": "hello"}

    def test_satisfies(self):
        s = RWMemorySpecification()
        log = [
            Operation("rd", "key1", None),
            Operation("wr", ("key1", "hello"), None),
            Operation("rd", "key1", "hello"),
        ]
        assert s.satisfies(log)

    def test_not_satisfies(self):
        s = RWMemorySpecification()
        log = [
            Operation("rd", "key1", None),
            Operation("wr", ("key1", "hello"), None),
            Operation("rd", "key1", "world"),
        ]
        assert not s.satisfies(log)

    def test_satisfies_ignore_instr(self):
        s = RWMemorySpecification()
        log = [
            Instruction("rd", "key1"),
            Instruction("wr", ("key1", "hello")),
            Operation("rd", "key1", "hello"),
        ]
        assert s.satisfies(log)


class TestHistory:
    def make_history_a(self):
        h = History(
            {
                "a": [Operation("wr", ("x", 1)), Operation("rd", "x", 2)],
                "b": [Operation("wr", ("x", 2)), Operation("rd", "x", 1)],
            }
        )
        return h

    def make_history_b(self):
        h = History(
            {
                "a": [
                    Operation("wr", ("z", 1)),
                    Operation("wr", ("x", 1)),
                    Operation("wr", ("y", 1)),
                ],
                "b": [
                    Operation("wr", ("x", 2)),
                    Operation("rd", "z", None),  # default value (0 in paper)
                    Operation("rd", "y", 1),
                    Operation("rd", "x", 2),
                ],
            }
        )
        return h

    def make_history_c(self):
        h = History(
            {
                "a": [Operation("wr", ("x", 1))],
                "b": [
                    Operation("wr", ("x", 2)),
                    Operation("rd", "x", 1),
                    Operation("rd", "x", 2),
                ],
            }
        )
        return h

    def make_history_d(self):
        h = History(
            {
                "a": [
                    Operation("wr", ("x", 1)),
                    Operation("rd", "y", None),  # default value
                    Operation("wr", ("y", 1)),
                    Operation("rd", "x", 1),
                ],
                "b": [
                    Operation("wr", ("x", 2)),
                    Operation("rd", "y", None),  # default value
                    Operation("wr", ("y", 2)),
                    Operation("rd", "x", 2),
                ],
            }
        )
        return h

    def make_history_e(self):
        h = History(
            {
                "a": [Operation("wr", ("x", 1)), Operation("wr", ("y", 1))],
                "b": [Operation("rd", "y", 1), Operation("wr", ("x", 2))],
                "c": [
                    Operation("rd", "x", 2),
                    Operation("rd", "x", 1),
                ],
            }
        )
        return h

    def test_cc_history_a(self):
        h = self.make_history_a()
        assert check_CC(h, RWMemorySpecification()).is_CC is True

    def test_cm_history_a(self):
        h = self.make_history_a()
        assert check_CM(h, RWMemorySpecification()).is_CM is True

    def test_cv_history_a(self):
        h = self.make_history_a()
        assert check_CCv(h, RWMemorySpecification()).is_CCv is False

    def test_cc_history_b(self):
        h = self.make_history_b()
        assert check_CC(h, RWMemorySpecification()).is_CC is True

    def test_cm_history_b(self):
        h = self.make_history_b()
        assert check_CM(h, RWMemorySpecification()).is_CM is False

    def test_cv_history_b(self):
        h = self.make_history_b()
        assert check_CCv(h, RWMemorySpecification()).is_CCv is True

    def test_cc_history_c(self):
        h = self.make_history_c()
        assert check_CC(h, RWMemorySpecification()).is_CC is True

    def test_cm_history_c(self):
        h = self.make_history_c()
        assert check_CM(h, RWMemorySpecification()).is_CM is False

    def test_cv_history_c(self):
        h = self.make_history_c()
        assert check_CCv(h, RWMemorySpecification()).is_CCv is False

    @pytest.mark.slow()
    def test_cc_history_d(self):
        h = self.make_history_d()
        assert check_CC(h, RWMemorySpecification()).is_CC is True

    @pytest.mark.slow()
    def test_cm_history_d(self):
        h = self.make_history_d()
        assert check_CM(h, RWMemorySpecification()).is_CM is True

    @pytest.mark.slow()
    def test_cv_history_d(self):
        h = self.make_history_d()
        assert check_CCv(h, RWMemorySpecification()).is_CCv is True

    @pytest.mark.slow()
    def test_cc_history_e(self):
        h = self.make_history_e()
        assert check_CC(h, RWMemorySpecification()).is_CC is False

    @pytest.mark.slow()
    def test_cm_history_e(self):
        h = self.make_history_e()
        assert check_CM(h, RWMemorySpecification()).is_CM is False

    @pytest.mark.slow()
    def test_cv_history_e(self):
        h = self.make_history_e()
        assert check_CCv(h, RWMemorySpecification()).is_CCv is False
