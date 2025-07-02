#!/bin/bash
# Script to activate the project environment
# Usage: source ./activate_env.sh

# Check if we're in the right directory
if [[ ! -f "venv/bin/activate" ]]; then
    echo "Error: venv not found. Make sure you're in the project root directory."
    exit 1
fi

# Activate the virtual environment
source venv/bin/activate

echo "✅ Virtual environment activated"
echo "Python path: $(which python)"
echo "Python version: $(python --version)"

# Set PYTHONPATH to include the project root
export PYTHONPATH="${PWD}:${PYTHONPATH}"
echo "PYTHONPATH set to include project root"