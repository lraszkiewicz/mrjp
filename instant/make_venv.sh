#!/usr/bin/env bash

python3 -m venv ./py3_venv && \
source py3_venv/bin/activate && \
pip3 install antlr4-python3-runtime
