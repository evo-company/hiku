#!/usr/bin/env bash

maturin develop --release || exit 1
pushd ../
pytest tests/benchmarks
popd
