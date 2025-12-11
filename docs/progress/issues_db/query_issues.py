import sqlite3
import argparse
import os

def query_issues(status=None, tier=None, category=None):
    db_path = os.path.join(os.path.dirname(__file__), 'issues.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    query = 'SELECT id, title, status, tier, category, dependencies, blocks, target_date FROM issues WHERE 1=1'
    params = []

    if status:
        query += ' AND status = ?'
        params.append(status)
    if tier:
        query += ' AND tier = ?'
        params.append(tier)
    if category:
        query += ' AND category = ?'
        params.append(category)

    c.execute(query, params)
    rows = c.fetchall()
    
    if not rows:
        print("No issues found matching the criteria.")
        conn.close()
        return

    # Get column names
    column_names = [description[0] for description in c.description]

    # Calculate maximum width for each column
    column_widths = {name: len(name) for name in column_names}
    for row in rows:
        for i, value in enumerate(row):
            column_widths[column_names[i]] = max(column_widths[column_names[i]], len(str(value)))

    # Print header
    header_line = " | ".join(name.ljust(column_widths[name]) for name in column_names)
    print(header_line)
    print("-+-".join("-" * column_widths[name] for name in column_names))

    # Print rows
    for row in rows:
        row_line = " | ".join(str(value).ljust(column_widths[column_names[i]]) for i, value in enumerate(row))
        print(row_line)

    conn.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Query the issues database.')
    parser.add_argument('--status', help='Filter by status (e.g., OPEN, COMPLETE)')
    parser.add_argument('--tier', help='Filter by tier (e.g., T1, T2)')
    parser.add_argument('--category', help='Filter by category')

    args = parser.parse_args()

    query_issues(status=args.status, tier=args.tier, category=args.category)
