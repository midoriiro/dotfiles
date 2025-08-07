#!/bin/bash

poetry run pytest \
    --capture=no \
    --verbose \
    --durations=0 \
    tests/test_binary_name.py::test_wheel