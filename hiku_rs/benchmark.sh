#!/usr/bin/env bash

maturin develop --release
pushd ../
pytest tests/benchmarks
popd
