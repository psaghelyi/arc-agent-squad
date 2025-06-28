#!/bin/bash
# This script activates the project's virtual environment
# Usage: source activate.sh

# Check if venv directory exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found!"
    echo "Setting up a new virtual environment in ./venv..."
    python3 -m venv venv
    
    echo "Installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt
    
    echo "Virtual environment setup complete!"
else
    echo "Activating existing virtual environment..."
    source venv/bin/activate
fi

# Show python location and version
echo "Using Python: $(which python)"
echo "Python version: $(python --version)"

# Reminder to run 'deactivate' to exit the virtual environment
echo "Virtual environment activated! Run 'deactivate' to exit." 