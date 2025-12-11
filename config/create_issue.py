#!/usr/bin/env python3
import re
import os

# Correctly locate issues.md relative to this script's location
ISSUES_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'docs', 'progress', 'issues.md'))

# Categories based on the structure of issues.md
CATEGORIES = {
    "1": ("Architecture & Design", "A"),
    "2": ("Scientific & Modeling", "M"),
    "3": ("Implementation & Reliability", "I"),
    "4": ("Data, Reproducibility & Archiving", "D"),
    "5": ("Testing, Validation & Tooling", "T"),
    "6": ("UX & UI", "U"),
}

# Tiers based on the structure of issues.md
TIERS = {
    "1": ("Tier 1 — Critical Issues", "T1"),
    "2": ("Tier 2 — Important Issues", "T2"),
    "3": ("Tier 3 — Lower-priority / exploratory issues", "T3"),
}

def get_next_issue_id(category_letter):
    """Finds the next available issue ID for a given category by reading the issues file."""
    try:
        with open(ISSUES_FILE_PATH, 'r') as f:
            content = f.read()
        
        # Regex to find all issue IDs for the given category, e.g., [A1], [A12]
        regex = re.compile(r'\[' + re.escape(category_letter) + r'(\d+)\]')
        matches = regex.findall(content)
        
        if not matches:
            return 1
            
        max_id = max(int(num) for num in matches)
        return max_id + 1
    except FileNotFoundError:
        # This case should ideally not be hit if the path is correct
        return 1

def get_user_input(prompt, choices):
    """Generic function to get a valid choice from the user."""
    while True:
        print(prompt)
        for key, value in choices.items():
            print(f"  {key}. {value}")
        
        choice = input("> ").strip()
        if choice in choices:
            return choice
        else:
            print("Invalid choice. Please try again.")

def create_new_issue():
    """Main function to guide the user through creating and adding a new issue."""
    
    print("--- Create New RPM-EE Issue ---")

    # 1. Get Tier
    tier_choice = get_user_input("Choose a priority tier:", {k: v[0] for k, v in TIERS.items()})
    _, tier_code = TIERS[tier_choice]
    tier_name_for_header = TIERS[tier_choice][0]

    # 2. Get Category
    category_choice = get_user_input("\nChoose a category:", {k: v[0] for k, v in CATEGORIES.items()})
    category_name, category_letter = CATEGORIES[category_choice]

    # 3. Get Title
    title = ""
    while not title:
        title = input("\nEnter the issue title: ").strip()
        if not title:
            print("Title cannot be empty.")

    # 4. Get Acceptance Criteria
    acceptance_criteria = input("Enter the acceptance criteria (single line): ").strip()
    if not acceptance_criteria:
        acceptance_criteria = "TBD"

    # 5. Generate Issue ID
    next_id = get_next_issue_id(category_letter)
    issue_id = f"[{category_letter}{next_id}]"

    # 6. Format the issue markdown
    # Example: - **[U8] Issues Addition**
    #            - Tier: T3 | Phase: Maintenance | Status: {TODO} | Dependencies: — | Blocks: — | Target Date: —
    #            - Acceptance Criteria: Python script and a shell command script that allows for easy adding and organizing of issues
    new_issue_md = (
        f"- **{issue_id} {title}**\n"
        f"  - Tier: {tier_code} | Phase: Maintenance | Status: {{TODO}} | Dependencies: — | Blocks: — | Target Date: —\n"
        f"  - Acceptance Criteria: {acceptance_criteria}\n"
    )

    # 7. Append to the file
    try:
        with open(ISSUES_FILE_PATH, 'r+') as f:
            lines = f.readlines()
            
            # Build the headers to search for
            tier_header = f"## {tier_name_for_header}"
            category_header = f"### {category_name} [{category_letter}#]"
            open_subheader = "#### Open"
            
            tier_index = -1
            category_index = -1
            open_subheader_index = -1
            
            # Find the line indices of the Tier, Category, and "Open" subheader
            for i, line in enumerate(lines):
                if tier_header in line:
                    tier_index = i
                    break # Found the right tier, start searching for category from here
            
            if tier_index != -1:
                for i, line in enumerate(lines[tier_index:], start=tier_index):
                    if category_header in line:
                        category_index = i
                        break # Found the right category
            
            if category_index != -1:
                for i, line in enumerate(lines[category_index:], start=category_index):
                    if open_subheader in line:
                        open_subheader_index = i
                        break # Found the "Open" section

            if open_subheader_index != -1:
                # Insert the new issue right after "#### Open"
                lines.insert(open_subheader_index + 1, new_issue_md)
                f.seek(0)
                f.writelines(lines)
                print(f"\n✅ Successfully added new issue {issue_id} to {os.path.basename(ISSUES_FILE_PATH)}")
            else:
                print(f"❌ Error: Could not find the section to add the issue.")
                print(f"   Looking for: '{tier_header}' -> '{category_header}' -> '{open_subheader}'")

    except FileNotFoundError:
        print(f"❌ Error: Could not find the issues file at {ISSUES_FILE_PATH}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    create_new_issue()
