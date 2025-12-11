#!/bin/bash
# This script runs the Python utility to create a new issue in issues.md

# Get the absolute path of the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

# Define the path to the Python script
PYTHON_SCRIPT="$SCRIPT_DIR/create_issue.py"

# Check if the Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: The script 'create_issue.py' was not found in the same directory."
    exit 1
fi

# Execute the Python script using the python3 interpreter
python3 "$PYTHON_SCRIPT"
