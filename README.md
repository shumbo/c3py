# c3py

<p align="center">
  <img src="https://github.com/shumbo/c3py/assets/10496155/08a6155d-0716-4c27-87cb-f2c0e29d510c" alt="C3PY" width="256px" height="256px">
</p>

Causal Consistency Checker in Python.

## Overview

C3PY is a Python library for checking the causal consistency of an execution history of a concurrent system. It is based on the paper ["On verifying causal consistency" by Bouajjani, et al.](https://dl.acm.org/doi/10.1145/3093333.3009888)

C3PY checks whether a given execution history is causally consistent provided the sequential specification of the system.

The library is still under active development and the API is subject to change. Please see the [tests](https://github.com/shumbo/c3py/blob/main/src/c3py/history_test.py) for usage examples.

## Development

### Setup

This repository uses [Rye](https://rye-up.com) for development. Install Rye and run the following command to start the development environment.

```sh
git clone https://github.com/shumbo/c3py.git
cd c3py
rye sync
```

### Lint and Format

Use `ruff` (which is bundled with Rye) to lint and format the code.

```sh
rye format
rye check
rye check --fix # to auto-fix some of the issues
```

### Test

This repository uses [pytest](https://docs.pytest.org/en/stable/) for testing. Run the following command to run the tests.

```sh
rye run pytest
# some tests are marked as slow, so you may want to run the following command to run all tests
rye run pytest --slow
```

To write a new test, create a new file suffixed with `_test.py` in the `src` directory and write a test function prefixed with `test_`. Please see the [pytest documentation](https://docs.pytest.org/en/stable/) for more information.
