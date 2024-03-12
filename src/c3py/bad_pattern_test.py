from c3py.bad_pattern import (
    BadPattern,
    WRMemoryHistory,
    find_cc_bad_pattern,
    find_ccv_bad_pattern,
)
from c3py.history import Operation


class TestWRMemoryHistory:
    def make_wrhistory_a(self):
        h = WRMemoryHistory(
            {
                "a": [Operation("wr", ("x", 1)), Operation("rd", "x", 2)],
                "b": [Operation("wr", ("x", 2)), Operation("rd", "x", 1)],
            }
        )
        return h

    def make_wrhistory_b(self):
        h = WRMemoryHistory(
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

    def make_wrhistory_c(self):
        h = WRMemoryHistory(
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

    def make_wrhistory_d(self):
        h = WRMemoryHistory(
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

    def make_wrhistory_e(self):
        h = WRMemoryHistory(
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

    def test_check_differentiated_h(self):
        h_b = self.make_wrhistory_b()
        assert h_b.check_differentiated_h()

        # Todo
        not_diff_h = WRMemoryHistory(
            {
                "a": [Operation("wr", ("x", 1)), Operation("rd", "x", 2)],
                "b": [Operation("wr", ("x", 1)), Operation("rd", "x", 1)],
            }
        )
        assert not not_diff_h.check_differentiated_h()

    def test_make_co_a(self):
        h = self.make_wrhistory_a()
        assert not h.bp
        assert h != BadPattern.CyclicCO
        assert h != BadPattern.ThinAirRead
        correct_co = set(
            (
                ("a.1", "a.2"),
                ("b.1", "b.2"),
                ("a.1", "b.2"),
                ("b.1", "a.2"),
            )
        )
        assert h.poset.G.edges() == correct_co

    def test_make_co_b(self):
        h = self.make_wrhistory_b()
        assert not h.bp
        assert h != BadPattern.CyclicCO
        assert h != BadPattern.ThinAirRead
        correct_co = set(
            (
                ("a.1", "a.2"),
                ("a.1", "a.3"),
                ("a.1", "b.3"),
                ("a.1", "b.4"),
                ("a.2", "a.3"),
                ("a.2", "b.3"),
                ("a.2", "b.4"),
                ("a.3", "b.3"),
                ("a.3", "b.4"),
                ("b.1", "b.2"),
                ("b.1", "b.3"),
                ("b.1", "b.4"),
                ("b.2", "b.3"),
                ("b.2", "b.4"),
                ("b.3", "b.4"),
            )
        )
        assert h.poset.G.edges() == correct_co

    def test_make_co_cyclic(self):
        h = WRMemoryHistory(
            {
                "a": [Operation("rd", "x", 1), Operation("wr", ("x", 1))],
                "b": [Operation("wr", ("x", 2)), Operation("rd", "x", 2)],
            }
        )
        assert h.bp == BadPattern.CyclicCO

    def test_make_co_thin_air_read(self):
        h = WRMemoryHistory(
            {
                "a": [Operation("wr", ("x", 1)), Operation("rd", "x", 2)],
                "b": [Operation("wr", ("x", 2)), Operation("rd", "y", 1)],
            }
        )
        assert h.bp == BadPattern.ThinAirRead

    def test_is_write_co_init_read_false(self):
        h_b = self.make_wrhistory_b()
        assert not h_b.is_write_co_init_read()

    def test_write_co_init_read(self):
        h = WRMemoryHistory(
            {"a": [Operation("wr", ("x", 1)), Operation("rd", "x", None)]}
        )
        assert h.is_write_co_init_read()

    def test_is_write_co_read_true(self):
        h = self.make_wrhistory_e()
        assert h.is_write_co_read()

    def test_is_write_co_read_false(self):
        h = self.make_wrhistory_a()
        assert not h.is_write_co_read()

    def test_cc_bad_pattern_a(self):
        h = self.make_wrhistory_a()
        assert h.check_differentiated_h()
        res = find_cc_bad_pattern(h)
        assert res.is_CC
        assert not res.bad_pattern

    def test_cc_bad_pattern_b(self):
        h = self.make_wrhistory_b()
        assert h.check_differentiated_h()
        res = find_cc_bad_pattern(h)
        assert res.is_CC
        assert not res.bad_pattern

    def test_cc_bad_pattern_c(self):
        h = self.make_wrhistory_c()
        assert h.check_differentiated_h()
        res = find_cc_bad_pattern(h)
        assert res.is_CC
        assert not res.bad_pattern

    def test_cc_bad_pattern_d(self):
        h = self.make_wrhistory_d()
        assert h.check_differentiated_h()
        res = find_cc_bad_pattern(h)
        assert res.is_CC
        assert not res.bad_pattern

    def test_cc_bad_pattern_e(self):
        h = self.make_wrhistory_e()
        assert h.check_differentiated_h()
        res = find_cc_bad_pattern(h)
        assert not res.is_CC
        assert res.bad_pattern == BadPattern.WriteCORead

    def test_ccv_bad_pattern_a(self):
        h = self.make_wrhistory_a()
        res = find_ccv_bad_pattern(h)
        assert not res.is_CCv
        assert res.bad_pattern == BadPattern.CyclicCF

    def test_ccv_bad_pattern_b(self):
        h = self.make_wrhistory_b()
        res = find_ccv_bad_pattern(h)
        assert res.is_CCv
        assert not res.bad_pattern

    def test_ccv_bad_pattern_c(self):
        h = self.make_wrhistory_c()
        res = find_ccv_bad_pattern(h)
        assert not res.is_CCv
        assert res.bad_pattern == BadPattern.CyclicCF

    def test_ccv_bad_pattern_d(self):
        h = self.make_wrhistory_d()
        res = find_ccv_bad_pattern(h)
        assert res.is_CCv
        assert not res.bad_pattern
