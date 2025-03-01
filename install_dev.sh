#!/bin/bash
# Script to install the package in development mode

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install package in development mode
echo "Installing package in development mode..."
pip install -e ".[dev,web]"

# Run tests
echo "Running tests..."
./tests/run_tests.py

echo "Installation complete!"
echo "To activate the virtual environment, run: source venv/bin/activate"
echo "To run the launcher, run: psychopy-gaze-launcher" 