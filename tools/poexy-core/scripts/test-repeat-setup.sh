#!/bin/bash

N=1000  # Set the number of repetitions here

# Setup with PIP ~22s
# Setup with UV ~8s

for ((i=1; i<=N; i++)); do
    echo "Run $i/$N"
    poetry run pytest \
        --exitfirst \
        --setup-only \
        --capture=no \
        --verbose \
        --durations=0 \
        tests/cases/core_functionality/test_default.py::test_wheel
done