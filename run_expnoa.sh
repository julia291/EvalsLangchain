#!/bin/bash
# Script to run ExpNoA.py using the .venv python environment

# Ensure we are in the project root
cd "$(dirname "$0")"

# Run the script
./.venv/bin/python src/ExpNoA.py
