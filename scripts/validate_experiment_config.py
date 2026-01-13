#!/usr/bin/env python3
"""
Validate experiment configuration files.

Checks YAML/JSON experiment config files for required fields and valid values.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml
except ImportError:
    print("Warning: PyYAML not installed, skipping YAML validation")
    yaml = None


REQUIRED_EXPERIMENT_FIELDS = {
    'name',
    'version',
}

OPTIONAL_EXPERIMENT_FIELDS = {
    'description',
    'author',
    'date',
    'preset',
    'episodes',
    'seed',
    'output_dir',
}


def validate_config(config: Dict[str, Any], filepath: Path) -> List[str]:
    """Validate experiment configuration and return errors."""
    errors = []
    
    # Check required fields
    missing = REQUIRED_EXPERIMENT_FIELDS - set(config.keys())
    if missing:
        errors.append(f"Missing required fields: {', '.join(sorted(missing))}")
    
    # Validate field types and values
    if 'name' in config and not isinstance(config['name'], str):
        errors.append(f"'name' must be string, got {type(config['name']).__name__}")
    
    if 'version' in config:
        if not isinstance(config['version'], (str, float, int)):
            errors.append(f"'version' must be string/number, got {type(config['version']).__name__}")
    
    if 'episodes' in config:
        if not isinstance(config['episodes'], int) or config['episodes'] < 1:
            errors.append(f"'episodes' must be positive integer, got {config.get('episodes')}")
    
    if 'preset' in config:
        valid_presets = ['neurotypical', 'asd_typical', 'adhd_typical', 'mdd_typical']
        if config['preset'] not in valid_presets:
            errors.append(f"'preset' must be one of {valid_presets}, got '{config['preset']}'")
    
    return errors


def load_yaml(filepath: Path) -> Dict[str, Any]:
    """Load YAML file."""
    if yaml is None:
        return {}
    with open(filepath, 'r') as f:
        return yaml.safe_load(f) or {}


def load_json(filepath: Path) -> Dict[str, Any]:
    """Load JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def main():
    """Validate experiment configuration files."""
    if len(sys.argv) < 2:
        print("Usage: validate_experiment_config.py <config_file> [<config_file> ...]")
        sys.exit(0)
    
    all_errors = []
    
    for filepath_str in sys.argv[1:]:
        filepath = Path(filepath_str)
        
        if not filepath.exists():
            print(f"✗ {filepath}: File not found")
            all_errors.append(f"{filepath}: not found")
            continue
        
        try:
            # Load config based on extension
            if filepath.suffix in ['.yaml', '.yml']:
                config = load_yaml(filepath)
            elif filepath.suffix == '.json':
                config = load_json(filepath)
            else:
                print(f"⊘ {filepath}: Skipping (not YAML/JSON)")
                continue
            
            # Skip if empty or not a dict
            if not config or not isinstance(config, dict):
                print(f"⊘ {filepath}: Skipping (empty or invalid structure)")
                continue
            
            # Validate
            errors = validate_config(config, filepath)
            
            if errors:
                print(f"✗ {filepath}:")
                for error in errors:
                    print(f"  {error}")
                all_errors.extend(errors)
            else:
                print(f"✓ {filepath}: OK")
        
        except Exception as e:
            print(f"✗ {filepath}: {e}")
            all_errors.append(str(e))
    
    if all_errors:
        print(f"\n✗ Validation failed with {len(all_errors)} error(s)")
        sys.exit(1)
    else:
        print(f"\n✓ All files validated successfully")
        sys.exit(0)


if __name__ == "__main__":
    main()
