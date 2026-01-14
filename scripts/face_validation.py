#!/usr/bin/env python3
"""
Face Validation: Compare Simulation Outputs to Clinical Patterns
=================================================================

Validates that preset behaviors match expected clinical profiles from literature.

Clinical Expectations:
- ASD: High stress reactivity, inflexible attention, sensory overwhelm
- ADHD: High RT variability, attention lapses, impulsivity
- MDD: Psychomotor slowing, anhedonia, sustained negative affect

Author: RPM-EE Clinical Validation Team
Date: 2026-01-14
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.presets import CLINICAL_PRESETS


class FaceValidation:
    """Face validation framework for clinical presets."""
    
    # Expected clinical patterns from literature
    EXPECTED_PATTERNS = {
        'asd_typical': {
            'stress_reactivity': {
                'expectation': 'elevated',
                'rationale': 'Corbett et al. (2009): ASD shows 2x cortisol response to social stress',
                'criteria': lambda v: v > 0.4,  # Higher than NT baseline
            },
            'attention_stability': {
                'expectation': 'inflexible_but_sustained',
                'rationale': 'ASD shows hyperfocus, difficulty disengaging (see v1.1 doc)',
                'criteria': lambda v: v > 0.85,  # Very stable
            },
            'switch_cost': {
                'expectation': 'high',
                'rationale': 'Set-shifting deficits in ASD (Hill 2004)',
                'criteria': lambda v: v > 0.20,  # Proportional cost >20%
            },
            # Note: sensory_threshold not implemented in current simulation
            # Would need sensory_threshold parameter in presets + processing in sensory.py
        },
        'adhd_typical': {
            'rt_variability': {
                'expectation': 'very_high',
                'rationale': 'Kofler et al. (2013) meta-analysis: 3x variability vs controls',
                'criteria': lambda v: v > 0.35,  # CV > 0.35
            },
            'attention_stability': {
                'expectation': 'low',
                'rationale': 'Sustained attention deficits core to ADHD',
                'criteria': lambda v: v < 0.7,
            },
            'vigilance_decrement': {
                'expectation': 'steep',
                'rationale': 'Rapid performance decline over time (Huang-Pollock 2012)',
                'criteria': lambda v: v > 0.012,  # Per-step decline
            },
            'wm_capacity': {
                'expectation': 'reduced',
                'rationale': 'Kasper et al. (2012): ~1 SD below controls',
                'criteria': lambda v: v < 3.5,  # items
            },
        },
        'mdd_typical': {
            'base_rt': {
                'expectation': 'slowed',
                'rationale': 'Tsourtos et al. (2002): 15-20% psychomotor slowing',
                'criteria': lambda v: v > 550,  # ms, slower than NT ~450-500
            },
            'positive_affect': {
                'expectation': 'very_low',
                'rationale': 'Treadway & Zald (2011): Anhedonia core symptom',
                'criteria': lambda v: v < 0.3,
            },
            'stress_baseline': {
                'expectation': 'elevated',
                'rationale': 'Burke et al. (2005) meta-analysis: Chronic HPA dysregulation',
                'criteria': lambda v: v > 0.5,
            },
            'reward_sensitivity': {
                'expectation': 'blunted',
                'rationale': 'Treadway & Zald (2011): Reduced reward responsiveness in depression',
                'criteria': lambda v: v < 0.20,  # Significantly reduced from NT ~0.25
            },
        },
        'neurotypical': {
            # Baseline expectations
            'wm_capacity': {
                'expectation': 'normal',
                'rationale': 'Cowan (2001): 4±1 items',
                'criteria': lambda v: 3.0 <= v <= 5.0,
            },
            'rt_variability': {
                'expectation': 'low',
                'rationale': 'Typical CV ~0.10-0.20',
                'criteria': lambda v: 0.10 <= v <= 0.25,
            },
            'stress_baseline': {
                'expectation': 'low',
                'rationale': 'Healthy resting cortisol',
                'criteria': lambda v: v < 0.4,
            },
        },
    }
    
    def __init__(self):
        self.results = {}
        
    def validate_preset(self, preset_name: str) -> Dict[str, Any]:
        """
        Validate a preset against expected clinical patterns.
        
        Args:
            preset_name: Name of preset to validate
            
        Returns:
            Validation results with pass/fail for each pattern
        """
        if preset_name not in CLINICAL_PRESETS:
            raise ValueError(f"Unknown preset: {preset_name}")
            
        preset_params = CLINICAL_PRESETS[preset_name]
        expected = self.EXPECTED_PATTERNS.get(preset_name, {})
        
        results = {
            'preset': preset_name,
            'total_patterns': len(expected),
            'patterns_passed': 0,
            'patterns_failed': 0,
            'details': [],
        }
        
        for param_name, pattern in expected.items():
            if param_name not in preset_params:
                results['details'].append({
                    'parameter': param_name,
                    'status': 'MISSING',
                    'expectation': pattern['expectation'],
                    'value': None,
                    'passed': False,
                })
                results['patterns_failed'] += 1
                continue
                
            param_value = preset_params[param_name]
            passed = pattern['criteria'](param_value)
            
            results['details'].append({
                'parameter': param_name,
                'status': 'PASS' if passed else 'FAIL',
                'expectation': pattern['expectation'],
                'rationale': pattern['rationale'],
                'value': param_value,
                'passed': passed,
            })
            
            if passed:
                results['patterns_passed'] += 1
            else:
                results['patterns_failed'] += 1
                
        results['pass_rate'] = results['patterns_passed'] / results['total_patterns'] if results['total_patterns'] > 0 else 0
        results['overall_status'] = 'PASS' if results['pass_rate'] >= 0.8 else 'NEEDS_REVIEW'
        
        return results
        
    def validate_all_presets(self) -> Dict[str, Any]:
        """Validate all presets and generate summary report."""
        all_results = {}
        
        for preset_name in CLINICAL_PRESETS.keys():
            all_results[preset_name] = self.validate_preset(preset_name)
            
        # Overall summary
        summary = {
            'total_presets': len(all_results),
            'presets_passing': sum(1 for r in all_results.values() if r['overall_status'] == 'PASS'),
            'presets_needing_review': sum(1 for r in all_results.values() if r['overall_status'] == 'NEEDS_REVIEW'),
            'preset_results': all_results,
        }
        
        return summary
        
    def generate_report(self, results: Dict[str, Any], output_path: Path = None) -> str:
        """Generate markdown report from validation results."""
        lines = [
            "# Face Validation Report: Clinical Presets",
            "",
            f"**Date:** 2026-01-14",
            f"**Validation Method:** Compare preset parameters to expected clinical patterns",
            "",
            "---",
            "",
            "## Summary",
            "",
            f"- **Total Presets Validated:** {results['total_presets']}",
            f"- **Presets Passing:** {results['presets_passing']} ✅",
            f"- **Presets Needing Review:** {results['presets_needing_review']} ⚠️",
            "",
            "---",
            "",
        ]
        
        # Detailed results for each preset
        for preset_name, preset_results in results['preset_results'].items():
            status_icon = "✅" if preset_results['overall_status'] == 'PASS' else "⚠️"
            lines.extend([
                f"## {preset_name.replace('_', ' ').title()} {status_icon}",
                "",
                f"**Overall Status:** {preset_results['overall_status']}",
                f"**Pass Rate:** {preset_results['pass_rate']:.1%} ({preset_results['patterns_passed']}/{preset_results['total_patterns']})",
                "",
                "| Parameter | Expectation | Value | Status | Rationale |",
                "|-----------|-------------|-------|--------|-----------|",
            ])
            
            for detail in preset_results['details']:
                status_sym = "✅" if detail['status'] == 'PASS' else "❌" if detail['status'] == 'FAIL' else "⚠️"
                param = detail['parameter']
                expect = detail['expectation']
                value = f"{detail['value']:.3f}" if isinstance(detail['value'], float) else str(detail['value'])
                if detail['value'] is None:
                    value = "N/A"
                rationale = detail.get('rationale', 'N/A')[:60]  # Truncate
                
                lines.append(f"| {param} | {expect} | {value} | {status_sym} | {rationale}... |")
                
            lines.extend(["", "---", ""])
            
        # Interpretation
        lines.extend([
            "## Interpretation",
            "",
            "### Passing Criteria",
            "- **PASS:** ≥80% of expected patterns matched",
            "- **NEEDS_REVIEW:** <80% match rate",
            "",
            "### What This Validates",
            "✅ **Face validity** - Parameters align with clinical expectations from literature",
            "✅ **Pattern consistency** - Each preset shows appropriate clinical profile",
            "✅ **Clinical plausibility** - Values fall within realistic ranges",
            "",
            "### What This Does NOT Validate",
            "❌ **Simulation behavior** - Need to run actual simulations (next step)",
            "❌ **Quantitative accuracy** - Need empirical data comparison",
            "❌ **Scale mappings** - Conversion formulas need separate validation",
            "",
            "---",
            "",
            "## Next Steps",
            "",
            "1. **For PASS presets:** Proceed to simulation validation",
            "2. **For NEEDS_REVIEW presets:**",
            "   - Review failed parameters",
            "   - Check literature support",
            "   - Adjust values if needed",
            "   - Re-run validation",
            "",
            "---",
            "",
            "## Recommendations",
            "",
        ])
        
        # Specific recommendations based on results
        for preset_name, preset_results in results['preset_results'].items():
            if preset_results['overall_status'] == 'NEEDS_REVIEW':
                failed = [d for d in preset_results['details'] if not d['passed']]
                lines.append(f"### {preset_name}")
                for detail in failed:
                    lines.append(f"- **{detail['parameter']}**: Expected {detail['expectation']}, got {detail['value']}")
                    lines.append(f"  - Action: Review literature and adjust if needed")
                lines.append("")
                
        report_text = "\n".join(lines)
        
        if output_path:
            output_path.write_text(report_text)
            print(f"✅ Report saved to: {output_path}")
            
        return report_text


def main():
    """Run face validation on all clinical presets."""
    print("=" * 70)
    print("Face Validation: Clinical Presets")
    print("=" * 70)
    print()
    
    validator = FaceValidation()
    
    # Run validation
    print("Validating all presets against expected clinical patterns...")
    results = validator.validate_all_presets()
    
    # Print summary
    print()
    print(f"✅ Validation complete!")
    print(f"   Presets passing: {results['presets_passing']}/{results['total_presets']}")
    print(f"   Presets needing review: {results['presets_needing_review']}/{results['total_presets']}")
    print()
    
    # Generate reports
    output_dir = project_root / "results" / "validation"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Markdown report
    report_path = output_dir / "face_validation_report.md"
    validator.generate_report(results, report_path)
    
    # JSON data
    json_path = output_dir / "face_validation_data.json"
    json_path.write_text(json.dumps(results, indent=2))
    print(f"✅ JSON data saved to: {json_path}")
    print()
    
    # Quick summary in terminal
    print("\nQuick Summary:")
    print("-" * 70)
    for preset_name, preset_results in results['preset_results'].items():
        status_icon = "✅" if preset_results['overall_status'] == 'PASS' else "⚠️"
        print(f"{status_icon} {preset_name:20s}: {preset_results['pass_rate']:>5.1%} pass rate")
    print("-" * 70)
    print()
    print(f"📄 Full report: {report_path}")
    print()


if __name__ == "__main__":
    main()
