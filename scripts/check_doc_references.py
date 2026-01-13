#!/usr/bin/env python3
"""
Check for broken references in documentation files.

Validates that images, links, and other assets referenced in markdown
files actually exist.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


def extract_references(content: str, filepath: Path) -> List[Tuple[str, str, int]]:
    """
    Extract image and link references from markdown.
    
    Returns list of (ref_type, path, line_number) tuples.
    """
    references = []
    
    # Image references: ![alt](path)
    img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    for match in re.finditer(img_pattern, content):
        line_num = content[:match.start()].count('\n') + 1
        references.append(('image', match.group(2), line_num))
    
    # Local file links: [text](path) - only check local files
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    for match in re.finditer(link_pattern, content):
        path = match.group(2)
        # Skip URLs
        if path.startswith(('http://', 'https://', 'mailto:', '#')):
            continue
        line_num = content[:match.start()].count('\n') + 1
        references.append(('link', path, line_num))
    
    # HTML img tags: <img src="path">
    html_img_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
    for match in re.finditer(html_img_pattern, content):
        line_num = content[:match.start()].count('\n') + 1
        references.append(('html_img', match.group(1), line_num))
    
    return references


def check_reference_exists(ref_path: str, doc_filepath: Path) -> bool:
    """Check if referenced file exists relative to document."""
    # Handle absolute paths from repo root
    if ref_path.startswith('/'):
        check_path = doc_filepath.parents[len(doc_filepath.parents) - 2] / ref_path.lstrip('/')
    else:
        # Relative to document location
        check_path = (doc_filepath.parent / ref_path).resolve()
    
    return check_path.exists()


def check_document(filepath: Path) -> List[str]:
    """Check a single document for broken references."""
    errors = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return [f"Failed to read file: {e}"]
    
    references = extract_references(content, filepath)
    
    for ref_type, ref_path, line_num in references:
        # Skip external URLs
        if ref_path.startswith(('http://', 'https://', 'mailto:')):
            continue
        
        # Check if file exists
        if not check_reference_exists(ref_path, filepath):
            errors.append(f"  Line {line_num}: Broken {ref_type} reference: {ref_path}")
    
    return errors


def main():
    """Check all provided markdown files."""
    if len(sys.argv) < 2:
        print("Usage: check_doc_references.py <file.md> [<file.md> ...]")
        sys.exit(0)
    
    all_errors = []
    
    for filepath_str in sys.argv[1:]:
        filepath = Path(filepath_str)
        
        if not filepath.exists():
            print(f"✗ {filepath}: File not found")
            all_errors.append(f"{filepath}: not found")
            continue
        
        errors = check_document(filepath)
        
        if errors:
            print(f"✗ {filepath}:")
            for error in errors:
                print(error)
            all_errors.extend(errors)
        else:
            print(f"✓ {filepath}: All references OK")
    
    if all_errors:
        print(f"\n⚠ Found {len(all_errors)} broken reference(s)")
        # Don't fail the commit for documentation issues - just warn
        sys.exit(0)
    else:
        print(f"\n✓ All references validated successfully")
        sys.exit(0)


if __name__ == "__main__":
    main()
