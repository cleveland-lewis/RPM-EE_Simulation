#!/usr/bin/env python3
"""
Parameter Sensitivity Analysis for Clinical Presets
Phase 3.1: Identify which parameters have the greatest impact on simulation outcomes
"""

import numpy as np
from pathlib import Path
import json
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

try:
    from rpm_ee.clinical import presets
    HAS_PRESETS = True
except ImportError:
    HAS_PRESETS = False
    print("Warning: Could not import rpm_ee.clinical.presets")


@dataclass
class SensitivityResult:
    """Results from sensitivity analysis"""
    parameter: str
    baseline_value: float
    perturbed_value: float
    perturbation_pct: float
    outcome_change: float
    sensitivity_index: float
    impact_category: str


class ParameterSensitivityAnalyzer:
    """
    Perform sensitivity analysis on clinical preset parameters.
    
    Uses One-At-a-Time (OAT) method:
    1. Start with baseline parameter set
    2. Perturb each parameter by ±10%, ±20%
    3. Measure impact on key outcomes
    4. Calculate sensitivity indices
    """
    
    def __init__(self, preset_name: str = "adhd_typical"):
        self.preset_name = preset_name
        self.baseline_params = self._load_baseline()
        self.perturbations = [-0.20, -0.10, 0.10, 0.20]  # ±10%, ±20%
        self.results = []
        
    def _load_baseline(self) -> Dict[str, float]:
        """Load baseline parameter values"""
        if HAS_PRESETS:
            return presets.get_preset(self.preset_name)
        else:
            # Fallback: use example ADHD values
            return {
                'base_rt': 0.450,
                'rt_variability': 0.45,
                'rt_slowing_rate': 0.002,
                'base_accuracy': 0.85,
                'accuracy_decline_rate': 0.001,
                'wm_capacity': 3.0,
                'wm_decay_rate': 0.018,
                'attention_stability': 0.60,
                'task_switch_cost': 0.35,
                'vigilance_decrement': 0.015,
                'stress_baseline': 0.55,
                'stress_reactivity': 0.75,
                'stress_recovery_rate': 0.015,
                'positive_affect_baseline': 0.55,
                'negative_affect_baseline': 0.55,
                'reward_sensitivity': 0.70,
                'prediction_error_gain': 0.80,
                'exploration_rate': 0.25,
            }
    
    def simulate_outcome(self, params: Dict[str, float]) -> Dict[str, float]:
        """
        Simulate outcomes given parameters.
        
        This is a MOCK function - replace with actual simulation calls.
        For now, we compute simple outcome metrics based on parameters.
        """
        # Mock outcomes based on parameter combinations
        outcomes = {
            # Response time outcomes
            'mean_rt': (
                params.get('base_rt', 0.4) * (1 + params.get('stress_baseline', 0.5) * 0.2)
            ),
            'rt_cv': params.get('rt_variability', 0.15),
            
            # Accuracy outcomes  
            'mean_accuracy': (
                params.get('base_accuracy', 0.95) * 
                (1 - params.get('stress_baseline', 0.5) * 0.1)
            ),
            
            # Working memory outcomes
            'wm_performance': (
                params.get('wm_capacity', 4.0) * 
                (1 - params.get('wm_decay_rate', 0.01) * 10)
            ),
            
            # Attention outcomes
            'sustained_attention': (
                params.get('attention_stability', 0.80) * 
                (1 - params.get('vigilance_decrement', 0.005) * 20)
            ),
            
            # Stress response
            'stress_response': (
                params.get('stress_baseline', 0.5) + 
                params.get('stress_reactivity', 0.5) * 0.5
            ),
            
            # Reward learning
            'reward_learning': (
                params.get('reward_sensitivity', 0.6) * 
                params.get('prediction_error_gain', 0.7)
            ),
        }
        
        return outcomes
    
    def perturb_parameter(self, param: str, perturbation: float) -> Dict[str, float]:
        """Create perturbed parameter set"""
        params = self.baseline_params.copy()
        
        if param in params:
            original = params[param]
            params[param] = original * (1 + perturbation)
            
            # Clamp to valid ranges (0-1 for most, some have different ranges)
            if param in ['wm_capacity']:
                params[param] = max(1.0, min(7.0, params[param]))
            else:
                params[param] = max(0.0, min(1.0, params[param]))
        
        return params
    
    def calculate_sensitivity(
        self,
        param: str,
        baseline_outcomes: Dict[str, float],
        perturbed_outcomes: Dict[str, float],
        perturbation: float
    ) -> List[SensitivityResult]:
        """Calculate sensitivity indices for all outcomes"""
        results = []
        
        for outcome_name, baseline_value in baseline_outcomes.items():
            perturbed_value = perturbed_outcomes[outcome_name]
            
            # Avoid division by zero
            if abs(baseline_value) < 1e-10:
                outcome_change_pct = 0.0
            else:
                outcome_change_pct = (perturbed_value - baseline_value) / baseline_value
            
            # Sensitivity index: (% change in outcome) / (% change in parameter)
            if abs(perturbation) < 1e-10:
                sensitivity = 0.0
            else:
                sensitivity = outcome_change_pct / perturbation
            
            # Categorize impact
            if abs(sensitivity) > 1.0:
                impact = "HIGH"
            elif abs(sensitivity) > 0.3:
                impact = "MODERATE"
            else:
                impact = "LOW"
            
            result = SensitivityResult(
                parameter=f"{param} → {outcome_name}",
                baseline_value=self.baseline_params.get(param, 0),
                perturbed_value=self.baseline_params.get(param, 0) * (1 + perturbation),
                perturbation_pct=perturbation * 100,
                outcome_change=outcome_change_pct * 100,
                sensitivity_index=sensitivity,
                impact_category=impact
            )
            
            results.append(result)
        
        return results
    
    def run_analysis(self) -> List[SensitivityResult]:
        """Run full sensitivity analysis"""
        print(f"\n{'='*70}")
        print(f"SENSITIVITY ANALYSIS: {self.preset_name}")
        print(f"{'='*70}\n")
        
        # Get baseline outcomes
        baseline_outcomes = self.simulate_outcome(self.baseline_params)
        
        print("Baseline Outcomes:")
        for outcome, value in baseline_outcomes.items():
            print(f"  {outcome}: {value:.4f}")
        print()
        
        # Test each parameter
        all_results = []
        
        for param in self.baseline_params.keys():
            print(f"Testing parameter: {param}")
            
            for perturbation in self.perturbations:
                # Perturb parameter
                perturbed_params = self.perturb_parameter(param, perturbation)
                
                # Simulate with perturbed parameters
                perturbed_outcomes = self.simulate_outcome(perturbed_params)
                
                # Calculate sensitivity
                results = self.calculate_sensitivity(
                    param,
                    baseline_outcomes,
                    perturbed_outcomes,
                    perturbation
                )
                
                all_results.extend(results)
        
        self.results = all_results
        return all_results
    
    def summarize_results(self) -> Dict[str, Any]:
        """Summarize sensitivity analysis results"""
        # Group by parameter
        param_impacts = {}
        
        for result in self.results:
            param = result.parameter.split(' → ')[0]
            
            if param not in param_impacts:
                param_impacts[param] = {
                    'high_impact_outcomes': [],
                    'moderate_impact_outcomes': [],
                    'low_impact_outcomes': [],
                    'max_sensitivity': 0.0,
                    'avg_sensitivity': 0.0,
                }
            
            # Track impacts
            if result.impact_category == "HIGH":
                outcome = result.parameter.split(' → ')[1]
                param_impacts[param]['high_impact_outcomes'].append(outcome)
            elif result.impact_category == "MODERATE":
                outcome = result.parameter.split(' → ')[1]
                param_impacts[param]['moderate_impact_outcomes'].append(outcome)
            else:
                outcome = result.parameter.split(' → ')[1]
                param_impacts[param]['low_impact_outcomes'].append(outcome)
            
            # Track max sensitivity
            if abs(result.sensitivity_index) > param_impacts[param]['max_sensitivity']:
                param_impacts[param]['max_sensitivity'] = abs(result.sensitivity_index)
        
        # Calculate averages
        for param, impacts in param_impacts.items():
            param_results = [r for r in self.results if r.parameter.startswith(param + ' →')]
            impacts['avg_sensitivity'] = np.mean([abs(r.sensitivity_index) for r in param_results])
        
        # Sort by importance
        sorted_params = sorted(
            param_impacts.items(),
            key=lambda x: (len(x[1]['high_impact_outcomes']), x[1]['max_sensitivity']),
            reverse=True
        )
        
        return dict(sorted_params)
    
    def generate_report(self, output_dir: Path):
        """Generate sensitivity analysis report"""
        output_dir.mkdir(exist_ok=True, parents=True)
        
        summary = self.summarize_results()
        
        # Create markdown report
        report_path = output_dir / f"sensitivity_analysis_{self.preset_name}.md"
        
        with open(report_path, 'w') as f:
            f.write(f"# Sensitivity Analysis: {self.preset_name}\n\n")
            f.write(f"**Date:** 2026-01-14\n")
            f.write(f"**Method:** One-At-a-Time (OAT) perturbation analysis\n")
            f.write(f"**Perturbations:** ±10%, ±20%\n\n")
            
            f.write("---\n\n")
            f.write("## Executive Summary\n\n")
            
            # Count high-impact parameters
            high_impact = [p for p, data in summary.items() if len(data['high_impact_outcomes']) > 0]
            moderate_impact = [p for p, data in summary.items() 
                             if len(data['high_impact_outcomes']) == 0 and len(data['moderate_impact_outcomes']) > 0]
            
            f.write(f"- **High-Impact Parameters:** {len(high_impact)}\n")
            f.write(f"- **Moderate-Impact Parameters:** {len(moderate_impact)}\n")
            f.write(f"- **Total Parameters Tested:** {len(summary)}\n\n")
            
            f.write("### High-Priority Parameters (Need Strong Validation)\n\n")
            for param in high_impact[:5]:
                data = summary[param]
                f.write(f"- **{param}**: {len(data['high_impact_outcomes'])} high-impact outcomes")
                f.write(f" (max sensitivity: {data['max_sensitivity']:.2f})\n")
            
            f.write("\n---\n\n")
            f.write("## Detailed Results\n\n")
            
            for param, data in summary.items():
                f.write(f"### {param}\n\n")
                f.write(f"- **Baseline Value:** {self.baseline_params.get(param, 'N/A')}\n")
                f.write(f"- **Max Sensitivity Index:** {data['max_sensitivity']:.3f}\n")
                f.write(f"- **Avg Sensitivity Index:** {data['avg_sensitivity']:.3f}\n")
                
                if data['high_impact_outcomes']:
                    f.write(f"- **HIGH Impact Outcomes:** {', '.join(set(data['high_impact_outcomes']))}\n")
                if data['moderate_impact_outcomes']:
                    f.write(f"- **MODERATE Impact Outcomes:** {', '.join(set(data['moderate_impact_outcomes']))}\n")
                
                f.write("\n")
            
            f.write("\n---\n\n")
            f.write("## Interpretation\n\n")
            f.write("**Sensitivity Index Interpretation:**\n")
            f.write("- SI > 1.0: HIGH impact (1% parameter change → >1% outcome change)\n")
            f.write("- 0.3 < SI < 1.0: MODERATE impact\n")
            f.write("- SI < 0.3: LOW impact\n\n")
            
            f.write("**Validation Priority:**\n")
            f.write("1. HIGH-impact parameters need strongest evidence (meta-analyses, large N)\n")
            f.write("2. MODERATE-impact parameters need good evidence (published studies)\n")
            f.write("3. LOW-impact parameters can use estimates or theoretical values\n\n")
        
        print(f"\n✓ Report saved to: {report_path}")
        
        # Save JSON data
        json_path = output_dir / f"sensitivity_data_{self.preset_name}.json"
        json_data = {
            'preset': self.preset_name,
            'baseline_params': self.baseline_params,
            'summary': summary,
            'results': [
                {
                    'parameter': r.parameter,
                    'perturbation_pct': r.perturbation_pct,
                    'outcome_change_pct': r.outcome_change,
                    'sensitivity_index': r.sensitivity_index,
                    'impact': r.impact_category,
                }
                for r in self.results
            ]
        }
        
        with open(json_path, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        print(f"✓ Data saved to: {json_path}")
        
        return report_path


def main():
    """Run sensitivity analysis for all presets"""
    print("="*70)
    print("CLINICAL PRESETS: PARAMETER SENSITIVITY ANALYSIS")
    print("="*70)
    
    output_dir = Path("results/sensitivity_analysis")
    
    # Analyze each preset
    presets_to_analyze = ["neurotypical", "asd_typical", "adhd_typical", "mdd_typical"]
    
    for preset_name in presets_to_analyze:
        print(f"\n\nAnalyzing: {preset_name}")
        print("-"*70)
        
        analyzer = ParameterSensitivityAnalyzer(preset_name)
        analyzer.run_analysis()
        report_path = analyzer.generate_report(output_dir)
        
        # Display top findings
        summary = analyzer.summarize_results()
        high_impact = [(p, d) for p, d in list(summary.items())[:5]]
        
        print(f"\nTop 5 High-Impact Parameters for {preset_name}:")
        for i, (param, data) in enumerate(high_impact, 1):
            print(f"  {i}. {param}: {len(data['high_impact_outcomes'])} high-impact outcomes")
    
    print(f"\n{'='*70}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*70}")
    print(f"\nResults saved to: {output_dir}/")
    print("\nNext steps:")
    print("1. Review high-impact parameters")
    print("2. Prioritize validation efforts for these parameters")
    print("3. Compare with Phase 2 evidence quality ratings")
    print("4. Update EVIDENCE_TABLE.md with sensitivity data")


if __name__ == "__main__":
    main()
