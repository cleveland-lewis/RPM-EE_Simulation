#!/bin/bash

# Path to the directory containing this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Function to update the database from issues.md
update_db() {
    echo "Updating database from issues.md..."
    python3 "$DIR/manage_db.py"
}

# Function to query the database
query_db() {
    python3 "$DIR/query_issues.py" "$@"
}

# Main command handling
case "$1" in
    update)
        update_db
        ;;
    query)
        shift # Remove 'query' from the arguments
        query_db "$@"
        ;;
    *)
        echo "Usage: $0 {update|query [options]}"
        exit 1
        ;;
esac
