#!/usr/bin/env python3
import sqlite3
import os
import argparse

# Define the path to the database file
DB_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'issues.db'))

def query_issues(status=None, tier=None, category=None):
    """Queries the issues database with optional filters for status, tier, and category."""
    
    if not os.path.exists(DB_FILE_PATH):
        print(f"Error: Database file not found at {DB_FILE_PATH}")
        print("Please run the manage_db.sh script first to create the database.")
        return

    try:
        conn = sqlite3.connect(DB_FILE_PATH)
        cursor = conn.cursor()

        query = "SELECT id, title, status, tier, category FROM issues"
        filters = []
        params = []

        if status:
            filters.append("status = ?")
            params.append(status)
        if tier:
            filters.append("tier = ?")
            params.append(tier)
        if category:
            filters.append("category_letter = ?")
            params.append(category)

        if filters:
            query += " WHERE " + " AND ".join(filters)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        if not rows:
            print("No issues found matching the criteria.")
        else:
            for row in rows:
                print(f"[{row[0]}] {row[1]} (Status: {row[2]}, Tier: {row[3]}, Category: {row[4]})")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

def main():
    """Main function to parse command-line arguments and query the database."""
    parser = argparse.ArgumentParser(description="Query the RPM-EE issues database.")
    
    parser.add_argument("--status", help="Filter by issue status (e.g., 'TODO', 'COMPLETE').")
    parser.add_argument("--tier", help="Filter by tier code (e.g., 'T1', 'T2').")
    parser.add_argument("--category", help="Filter by category letter (e.g., 'A', 'U').")

    args = parser.parse_args()

    query_issues(status=args.status, tier=args.tier, category=args.category)

if __name__ == "__main__":
    main()
