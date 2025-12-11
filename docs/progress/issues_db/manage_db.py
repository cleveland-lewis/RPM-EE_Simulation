import sqlite3
import re
import os

def create_database():
    db_path = os.path.join(os.path.dirname(__file__), 'issues.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS issues (
            id TEXT PRIMARY KEY,
            tier TEXT,
            phase TEXT,
            status TEXT,
            dependencies TEXT,
            blocks TEXT,
            target_date TEXT,
            title TEXT,
            acceptance_criteria TEXT,
            notes TEXT,
            category TEXT
        )
    ''')

    conn.commit()
    conn.close()

def parse_and_store_issues():
    issues_md_path = os.path.join(os.path.dirname(__file__), '..', 'issues.md')
    db_path = os.path.join(os.path.dirname(__file__), 'issues.db')

    with open(issues_md_path, 'r') as f:
        content = f.read()

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('DELETE FROM issues')  # Clear existing issues

    # Regex to find issue blocks
    issue_blocks = re.findall(r'-\s\*\*\[(.+?)\]\s(.+?)\*\*\s+-\sTier:\s(T\d+)\s\|\sPhase:\s(.+?)\s\|\sStatus:\s{(.+?)}\s\|\sDependencies:\s(.+?)\s\|\sBlocks:\s(.+?)\s\|\sTarget Date:\s(.+?)\s+-\sAcceptance Criteria:\s(.+?)(?:\s+-\sNotes:\s(.+?))?(?=\n-\s\*\*\[|\Z)', content, re.DOTALL)

    for block in issue_blocks:
        issue_id, title, tier, phase, status, dependencies, blocks, target_date, acceptance_criteria, notes = block
        
        # Extract category from the preceding header
        # This is a bit fragile and might need adjustment based on the exact format
        category_match = re.search(r'###\s(.+?)\s\[', content[:content.find(issue_id)])
        category = category_match.group(1).strip() if category_match else 'Uncategorized'

        c.execute('''
            INSERT INTO issues (id, tier, phase, status, dependencies, blocks, target_date, title, acceptance_criteria, notes, category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (issue_id.strip(), tier.strip(), phase.strip(), status.strip(), dependencies.strip(), blocks.strip(), target_date.strip(), title.strip(), acceptance_criteria.strip(), notes.strip() if notes else '', category))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_database()
    parse_and_store_issues()
    print("Database 'issues.db' has been created and populated.")
