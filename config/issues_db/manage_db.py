#!/usr/bin/env python3
import sqlite3
import re
import os
from markdown_it import MarkdownIt
from mdit_py_plugins.front_matter import front_matter_plugin

ISSUES_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'progress', 'issues.md'))
DB_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'issues.db'))

def create_database():
    """Creates the SQLite database and the issues table if they don't already exist."""
    try:
        conn = sqlite3.connect(DB_FILE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("DROP TABLE IF EXISTS issues")

        cursor.execute("""
        CREATE TABLE issues (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            tier TEXT,
            tier_name TEXT,
            category TEXT,
            category_letter TEXT,
            status TEXT,
            phase TEXT,
            dependencies TEXT,
            blocks TEXT,
            target_date TEXT,
            acceptance_criteria TEXT,
            completion_notes TEXT
        )
        """)
        
        conn.commit()
        print(f"Database created successfully at {DB_FILE_PATH}")
        return conn

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during database creation: {e}")
        return None

def parse_issues_md():
    """Parses the issues.md file and returns a list of issue dictionaries."""
    
    try:
        with open(ISSUES_FILE_PATH, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: issues.md file not found at {ISSUES_FILE_PATH}")
        return []

    md = MarkdownIt().use(front_matter_plugin)
    tokens = md.parse(content)
    
    issues = []
    current_tier_name = "Unknown"
    current_category_name = "Unknown"
    current_category_letter = "Unknown"

    for i, token in enumerate(tokens):
        if token.type == 'heading_open':
            if token.tag == 'h2':
                current_tier_name = tokens[i+1].content
            elif token.tag == 'h3':
                match = re.search(r'(.+?) \[(.+?)#\]', tokens[i+1].content)
                if match:
                    current_category_name = match.group(1).strip()
                    current_category_letter = match.group(2).strip()
        elif token.type == 'list_item_open':
            issue_content = ""
            for j in range(i + 1, len(tokens)):
                if tokens[j].type == 'list_item_close':
                    break
                if tokens[j].content:
                    issue_content += tokens[j].content + "\n"
            
            id_title_match = re.search(r'\*\*(\[[A-Z]\d+\])\s*(.+?)\*\*', issue_content)
            if id_title_match:
                details_match = re.search(r'Tier: (\w+)\s*\|\s*Phase: (.+?)\s*\|\s*Status: {(.+?)}\s*\|\s*Dependencies: (.+?)\s*\|\s*Blocks: (.+?)\s*\|\s*Target Date: (.+?)\s*', issue_content)
                acceptance_match = re.search(r'Acceptance Criteria: (.+?)', issue_content)
                completion_match = re.search(r'Completion Notes: (.+?)', issue_content)

                issue_data = {
                    "id": id_title_match.group(1).strip(),
                    "title": id_title_match.group(2).strip(),
                    "tier_name": current_tier_name,
                    "category": current_category_name,
                    "category_letter": current_category_letter,
                    "tier": details_match.group(1).strip() if details_match else "N/A",
                    "phase": details_match.group(2).strip() if details_match else "N/A",
                    "status": details_match.group(3).strip() if details_match else "N/A",
                    "dependencies": details_match.group(4).strip() if details_match else "N/A",
                    "blocks": details_match.group(5).strip() if details_match else "N/A",
                    "target_date": details_match.group(6).strip() if details_match else "N/A",
                    "acceptance_criteria": acceptance_match.group(1).strip() if acceptance_match else "N/A",
                    "completion_notes": completion_match.group(1).strip() if completion_match else "N/A",
                }
                issues.append(issue_data)
                
    return issues

def populate_database(conn, issues):
    """Populates the database with the parsed issues."""
    if not conn or not issues:
        print("Connection or issues list is empty. Aborting population.")
        return

    cursor = conn.cursor()
    
    for issue in issues:
        try:
            cursor.execute("""
            INSERT INTO issues (
                id, title, tier, tier_name, category, category_letter, status, phase, 
                dependencies, blocks, target_date, acceptance_criteria, completion_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                issue['id'], issue['title'], issue['tier'], issue['tier_name'], issue['category'],
                issue['category_letter'], issue['status'], issue['phase'], issue['dependencies'],
                issue['blocks'], issue['target_date'], issue['acceptance_criteria'], issue['completion_notes']
            ))
        except sqlite3.IntegrityError:
            print(f"Warning: Issue with ID {issue['id']} already exists. Skipping.")
        except sqlite3.Error as e:
            print(f"Database error while inserting issue {issue['id']}: {e}")

    conn.commit()
    print(f"Successfully inserted/updated {len(issues)} issues into the database.")

def write_issues_md(conn):
    """Writes the issues from the database back to the issues.md file."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM issues")
    issues = cursor.fetchall()

    with open(ISSUES_FILE_PATH, 'w') as f:
        # This is a simplified writer. A more robust implementation would preserve the original file structure.
        for issue in issues:
            f.write(f"- **{issue[0]} {issue[1]}**\n")
            f.write(f"  - Tier: {issue[2]} | Phase: {issue[7]} | Status: {{{issue[6]}}} | Dependencies: {issue[8]} | Blocks: {issue[9]} | Target Date: {issue[10]}\n")
            f.write(f"  - Acceptance Criteria: {issue[11]}\n")
            if issue[12]:
                f.write(f"  - Completion Notes: {issue[12]}\n")

def main():
    """Main function to orchestrate the database creation and population."""
    print("Starting issue database management...")
    
    conn = create_database()
    
    if conn:
        issues = parse_issues_md()
        
        if issues:
            populate_database(conn, issues)
            write_issues_md(conn)
        else:
            print("No issues were parsed from the markdown file.")
            
        conn.close()
        print("Database connection closed.")
    else:
        print("Failed to create or connect to the database.")

if __name__ == "__main__":
    main()
