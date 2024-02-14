# c3py

<p align="center">
  <img src="https://github.com/shumbo/c3py/assets/10496155/08a6155d-0716-4c27-87cb-f2c0e29d510c" alt="C3PY" width="256px" height="256px">
</p>

Causal Consistency Checker in Python.

## Overview

C3PY is a Python library for checking the causal consistency of an execution history of a concurrent system. It is based on the paper ["On verifying causal consistency" by Bouajjani, et al.](https://dl.acm.org/doi/10.1145/3093333.3009888)

C3PY checks whether a given execution history is causally consistent provided the sequential specification of the system.

The library is still under active development and the API is subject to change. Please see the [tests](https://github.com/shumbo/c3py/blob/main/src/c3py/history_test.py) for usage examples.
