#!/usr/bin/env python3
"""
Validate clinical presets configuration.

This script checks that all presets in src/presets.py are properly defined
with all required parameters and valid values.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from presets import CLINICAL_PRESETS, get_preset, list_presets
except ImportError:
    print("✗ Failed to import presets module")
    sys.exit(1)


# Required parameters for each preset
REQUIRED_PARAMS = {
    # Response time
    'base_rt',
    'rt_variability',
    'rt_slowing',
    # Accuracy
    'base_accuracy',
    'accuracy_decline',
    # Working memory
    'wm_capacity',
    'wm_decay_rate',
    # Attention
    'attention_stability',
    'switch_cost',
    'vigilance_decrement',
    # Stress
    'stress_baseline',
    'stress_reactivity',
    'stress_recovery',
    # Emotion
    'positive_affect',
    'negative_affect',
    'reward_sensitivity',
    # Learning
    'prediction_error_gain',
    'exploration_rate',
}


def validate_preset(name: str, params: dict) -> list[str]:
    """Validate a single preset and return list of errors."""
    errors = []
    
    # Check all required parameters present
    missing = REQUIRED_PARAMS - set(params.keys())
    if missing:
        errors.append(f"  Missing parameters: {', '.join(sorted(missing))}")
    
    # Validate parameter ranges
    for param, value in params.items():
        if not isinstance(value, (int, float)):
            errors.append(f"  {param}: must be numeric, got {type(value).__name__}")
            continue
        
        # Check range constraints
        if param in ['base_rt'] and value < 0:
            errors.append(f"  {param}: must be non-negative, got {value}")
        elif param in ['rt_variability', 'base_accuracy', 'accuracy_decline'] and not (0 <= value <= 1):
            errors.append(f"  {param}: must be in [0,1], got {value}")
        elif param in ['wm_capacity'] and value < 1:
            errors.append(f"  {param}: must be >= 1, got {value}")
        elif param in ['wm_decay_rate'] and not (0 <= value <= 1):
            errors.append(f"  {param}: must be in [0,1], got {value}")
        elif param.endswith('_stability') and not (0 <= value <= 1):
            errors.append(f"  {param}: must be in [0,1], got {value}")
        elif param.endswith('_cost') and not (0 <= value <= 1):
            errors.append(f"  {param}: must be in [0,1], got {value}")
        elif param.startswith('stress_') and param != 'stress_recovery' and not (0 <= value <= 1):
            errors.append(f"  {param}: must be in [0,1], got {value}")
        elif param.endswith('_affect') and not (0 <= value <= 1):
            errors.append(f"  {param}: must be in [0,1], got {value}")
        elif param.endswith('_sensitivity') and not (0 <= value <= 1):
            errors.append(f"  {param}: must be in [0,1], got {value}")
        elif param.endswith('_rate') and param != 'wm_decay_rate' and not (0 <= value <= 1):
            errors.append(f"  {param}: must be in [0,1], got {value}")
    
    return errors


def main():
    """Validate all clinical presets."""
    print("Validating clinical presets...")
    print()
    
    all_errors = []
    presets = list_presets()
    
    if not presets:
        print("✗ No presets found!")
        sys.exit(1)
    
    for preset_name in presets:
        try:
            params = get_preset(preset_name)
            errors = validate_preset(preset_name, params)
            
            if errors:
                print(f"✗ {preset_name}:")
                for error in errors:
                    print(error)
                all_errors.extend(errors)
            else:
                print(f"✓ {preset_name}: OK ({len(params)} parameters)")
        except Exception as e:
            print(f"✗ {preset_name}: {e}")
            all_errors.append(str(e))
    
    print()
    if all_errors:
        print(f"✗ Validation failed with {len(all_errors)} error(s)")
        sys.exit(1)
    else:
        print(f"✓ All {len(presets)} presets validated successfully")
        sys.exit(0)


if __name__ == "__main__":
    main()
