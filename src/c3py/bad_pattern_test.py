from c3py.bad_pattern import BadPattern, WRMemoryHistory
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

        not_diff_h = WRMemoryHistory(
            {
                "a": [Operation("wr", ("x", 1)), Operation("rd", "x", 2)],
                "b": [Operation("wr", ("x", 1)), Operation("rd", "x", 1)],
            }
        )
        assert not not_diff_h.check_differentiated_h()

    def test_make_co_a(self):
        h = self.make_wrhistory_a()
        h = h.make_co()
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
        h = h.make_co()
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
        h = h.make_co()
        assert h == BadPattern.CyclicCO

    def test_is_write_co_init_read_false(self):
        h_b = self.make_wrhistory_b()
        h_b = h_b.make_co()
        assert not h_b.is_write_co_init_read()

    def test_is_write_co_init_read_true(self):
        h = WRMemoryHistory(
            {
                "a": [Operation("wr", ("x", 1)), Operation("rd", "x", None)]
            }
        )
        h = h.make_co()
        assert h.is_write_co_init_read()

    def test_is_thin_air_read_false(self):
        h = self.make_wrhistory_a()
        h = h.make_co()
        assert not h.is_thin_air_read()

    def test_is_thin_air_read_true(self):
        h = WRMemoryHistory(
            {
                "a": [Operation("wr", ("x", 1)), Operation("rd", "x", 2)],
                "b": [Operation("wr", ("x", 2)), Operation("rd", "y", 1)],
            }
        )
        h.make_co()
        assert h.is_thin_air_read

    def test_is_write_co_read_true(self):
        h = self.make_wrhistory_e()
        h = h.make_co()
        assert h.is_write_co_read()

    def test_is_write_co_read_false(self):
        h = self.make_wrhistory_a()
        h = h.make_co()
        assert not h.is_write_co_read()
