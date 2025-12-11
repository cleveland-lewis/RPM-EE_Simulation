#!/bin/bash
# This script runs the Python utility to query the issues database.

# Get the absolute path of the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

# Define the path to the Python script
PYTHON_SCRIPT="$SCRIPT_DIR/query_issues.py"

# Check if the Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: The script 'query_issues.py' was not found in the same directory."
    exit 1
fi

# Execute the Python script with all command-line arguments passed to this script
python3 "$PYTHON_SCRIPT" "$@"
