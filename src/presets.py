"""
Clinical Presets for RPM-EE v1.1

This module defines empirically-grounded clinical population presets based
on peer-reviewed literature from cognitive psychology and clinical neuroscience.

All parameters are based on clinical observables:
- Response time (RT) metrics
- Accuracy/error rates
- Working memory capacity
- Attention/executive function measures
- Stress reactivity and regulation

NO neuroimaging or biomarker data is used - only behavioral/clinical measures.
"""

from typing import Dict, List, Optional

__all__ = [
    'CLINICAL_PRESETS',
    'PARAMETER_CONFIDENCE',
    'get_preset',
    'list_presets',
    'get_preset_description',
    'get_parameter_confidence',
    'get_preset_summary',
]

# =============================================================================
# CLINICAL FOUNDATIONS (Behavioral Literature Only)
# =============================================================================
#
# NEUROTYPICAL (NT):
#   • RT: 400-600ms (simple tasks), 600-900ms (complex tasks) [Ratcliff & McKoon, 2008]
#   • Accuracy: 85-95% typical [Luce, 1986]
#   • Working memory: 4±1 items [Cowan, 2001 - modern consensus]
#   • Stress: Moderate reactivity, adaptive recovery [McEwen, 1998]
#   • Attentional control: Flexible, goal-directed [Posner & Petersen, 1990]
#
# AUTISM SPECTRUM DISORDER (ASD):
#   • RT: 10-15% slower than NT [Happé & Frith, 2006]
#   • Accuracy: Comparable mean but higher variability [Geurts et al., 2009]
#   • Working memory: Intact capacity, impaired manipulation [Steele et al., 2007]
#   • Stress: Elevated baseline, prolonged recovery [Corbett et al., 2009]
#   • Attentional switching: Reduced flexibility [Yerys et al., 2009; Geurts et al., 2009]
#   • Sensory reactivity: Heightened sensitivity [Robertson & Baron-Cohen, 2017]
#
# ADHD (ATTENTION-DEFICIT/HYPERACTIVITY DISORDER):
#   • RT variability: 35-50% higher (IIV) [Klein et al., 2006; Kofler et al., 2013]
#   • Omission errors: 2-3x higher [Kofler et al., 2013]
#   • Working memory: Reduced by ~1 item relative to NT [Kasper et al., 2012]
#   • Sustained attention: Vigilance decrements over time [Huang-Pollock et al., 2012]
#   • Stress: Impaired regulation, faster reactivity [Lackschewitz et al., 2008]
#   • Temporal processing: Delay aversion [Sonuga-Barke, 2005]
#
# MAJOR DEPRESSIVE DISORDER (MDD):
#   • RT: 15-20% slower (psychomotor slowing) [Tsourtos et al., 2002]
#   • Accuracy: 5-10% reduction [Porter et al., 2003]
#   • Working memory: Reduced by ~0.5 items relative to NT [Christopher & MacDonald, 2005]
#   • Affect: Anhedonia (blunted positive affect) [Treadway & Zald, 2011]
#   • Stress: Elevated cortisol, HPA dysregulation [Burke et al., 2005]
#   • Cognitive control: Impaired, higher error rates [Snyder, 2013]
#   • Rumination: Increased internal focus [Nolen-Hoeksema, 2000]
#
# =============================================================================

CLINICAL_PRESETS: Dict[str, Dict[str, float]] = {
    # =========================================================================
    # NEUROTYPICAL BASELINE
    # =========================================================================
    'neurotypical': {
        # Response time parameters (ms)
        'base_rt': 500.0,          # Baseline RT for simple tasks
        'rt_variability': 0.15,    # Coefficient of variation (CV)
        'rt_slowing': 1.0,         # Multiplier (1.0 = no slowing)
        
        # Accuracy parameters
        'base_accuracy': 0.90,     # 90% baseline accuracy
        'accuracy_decline': 0.05,  # Decline under load
        
        # Working memory
        'wm_capacity': 4.0,        # Items (Cowan's 4±1, modern consensus)
        'wm_decay_rate': 0.01,     # Per-tick decay
        
        # Attention/executive function
        'attention_stability': 0.85,    # Sustained attention
        'switch_cost': 0.10,            # Cost of switching attention
        'vigilance_decrement': 0.01,    # Vigilance decline per unit time
        
        # Stress and regulation
        'stress_baseline': 0.30,        # Baseline stress level
        'stress_reactivity': 0.50,      # Reactivity to stressors
        'stress_recovery': 0.15,        # Recovery rate
        
        # Emotional/motivational
        'positive_affect': 0.60,        # Baseline positive affect
        'negative_affect': 0.20,        # Baseline negative affect
        'reward_sensitivity': 0.70,     # Reward responsiveness
        
        # Prediction/learning
        'prediction_error_gain': 1.0,   # Learning from errors
        'exploration_rate': 0.20,       # Exploratory behavior
    },
    
    # =========================================================================
    # AUTISM SPECTRUM DISORDER (ASD)
    # =========================================================================
    'asd_typical': {
        # RT: 10-15% slower, comparable variability
        'base_rt': 575.0,          # +15% slower (500 * 1.15)
        'rt_variability': 0.18,    # Slightly higher variability
        'rt_slowing': 1.15,
        
        # Accuracy: comparable mean, higher variability
        'base_accuracy': 0.88,     # Slightly lower
        'accuracy_decline': 0.08,  # More affected by load
        
        # Working memory: intact capacity, impaired manipulation
        'wm_capacity': 4.0,        # Normal capacity (Cowan 2001)
        'wm_decay_rate': 0.015,    # Faster decay under manipulation
        
        # Attention: reduced flexibility
        'attention_stability': 0.80,    # Good sustained attention
        'switch_cost': 0.25,            # Higher switching cost
        'vigilance_decrement': 0.008,   # Better sustained attention
        
        # Stress: elevated baseline, prolonged recovery
        'stress_baseline': 0.50,        # Elevated baseline
        'stress_reactivity': 0.60,      # Higher reactivity
        'stress_recovery': 0.08,        # Slower recovery
        
        # Emotional: heightened sensory reactivity
        'positive_affect': 0.50,        # Lower positive affect
        'negative_affect': 0.35,        # Higher negative affect
        'reward_sensitivity': 0.55,     # Reduced reward sensitivity
        
        # Prediction: intact but less flexible
        'prediction_error_gain': 0.90,  # Slightly reduced
        'exploration_rate': 0.12,       # Less exploratory
    },
    
    # =========================================================================
    # ADHD (ATTENTION-DEFICIT/HYPERACTIVITY DISORDER)
    # =========================================================================
    'adhd_typical': {
        # RT: normal mean but 35-50% higher variability
        'base_rt': 520.0,          # Slightly faster (impulsive)
        'rt_variability': 0.45,    # MUCH higher variability (IIV)
        'rt_slowing': 1.04,        # Slightly slower on average
        
        # Accuracy: lower, more omission errors
        'base_accuracy': 0.80,     # Lower baseline (more errors)
        'accuracy_decline': 0.12,  # Steeper decline under load
        
        # Working memory: reduced capacity
        'wm_capacity': 3.0,        # Reduced ~1 item below NT (proportional)
        'wm_decay_rate': 0.018,    # Faster decay
        
        # Attention: poor sustained attention, high distractibility
        'attention_stability': 0.60,    # Poor sustained attention
        'switch_cost': 0.08,            # Lower switching cost (hyper-switching)
        'vigilance_decrement': 0.025,   # Steep vigilance decrement
        
        # Stress: impaired regulation
        'stress_baseline': 0.35,        # Moderate baseline
        'stress_reactivity': 0.75,      # High reactivity
        'stress_recovery': 0.10,        # Moderate recovery
        
        # Emotional: heightened reactivity
        'positive_affect': 0.55,        # Moderate
        'negative_affect': 0.30,        # Moderate
        'reward_sensitivity': 0.85,     # High reward sensitivity
        
        # Prediction: high exploration, impulsive
        'prediction_error_gain': 1.20,  # Over-reactive to errors
        'exploration_rate': 0.40,       # Highly exploratory/impulsive
    },
    
    # =========================================================================
    # MAJOR DEPRESSIVE DISORDER (MDD)
    # =========================================================================
    'mdd_typical': {
        # RT: 15-20% psychomotor slowing
        'base_rt': 600.0,          # +20% slower (500 * 1.20)
        'rt_variability': 0.20,    # Moderately increased
        'rt_slowing': 1.20,
        
        # Accuracy: 5-10% reduction
        'base_accuracy': 0.82,     # Reduced accuracy
        'accuracy_decline': 0.10,  # Higher decline under load
        
        # Working memory: impaired especially under load
        'wm_capacity': 3.5,        # Reduced ~0.5 items below NT (proportional)
        'wm_decay_rate': 0.022,    # Faster decay
        
        # Attention: impaired cognitive control
        'attention_stability': 0.65,    # Poor sustained attention
        'switch_cost': 0.18,            # Higher switching cost
        'vigilance_decrement': 0.020,   # Higher vigilance decrement
        
        # Stress: HPA dysregulation, elevated cortisol
        'stress_baseline': 0.55,        # Elevated baseline
        'stress_reactivity': 0.65,      # High reactivity
        'stress_recovery': 0.06,        # Very slow recovery
        
        # Emotional: anhedonia (blunted positive affect)
        'positive_affect': 0.25,        # Severely reduced (anhedonia)
        'negative_affect': 0.55,        # Elevated negative affect
        'reward_sensitivity': 0.35,     # Severely reduced
        
        # Prediction: rumination, reduced exploration
        'prediction_error_gain': 0.70,  # Blunted learning
        'exploration_rate': 0.08,       # Reduced exploration
    },
}


# =============================================================================
# PARAMETER CONFIDENCE LEVELS
# =============================================================================
# Evidence quality for each parameter:
# - HIGH: Meta-analysis or multiple direct studies with quantitative values
# - MODERATE: Single study or indirect evidence with reasonable inference
# - LOW: Theoretical estimate or no direct empirical measurement

PARAMETER_CONFIDENCE: Dict[str, Dict[str, str]] = {
    'neurotypical': {
        'base_rt': 'HIGH',              # Ratcliff & McKoon (2008) - comprehensive review
        'rt_variability': 'MODERATE',   # Typical CV range from multiple studies
        'rt_slowing': 'HIGH',           # N/A for baseline (multiplier=1.0)
        'base_accuracy': 'MODERATE',    # Luce (1986) - general cognitive psych data
        'accuracy_decline': 'MODERATE', # Load effects well-documented in literature
        'wm_capacity': 'HIGH',          # Cowan (2001) - seminal work, widely replicated
        'wm_decay_rate': 'LOW',         # Estimated, no direct per-tick measure
        'attention_stability': 'LOW',   # Theoretical estimate from attention literature
        'switch_cost': 'LOW',           # No specific quantitative value from sources
        'vigilance_decrement': 'LOW',   # Rate not quantified, estimated from theory
        'stress_baseline': 'LOW',       # Scale mapping (cortisol → 0-1) unclear
        'stress_reactivity': 'LOW',     # Scale mapping unclear, theoretical estimate
        'stress_recovery': 'LOW',       # No time-course data for recovery rates
        'positive_affect': 'LOW',       # Theoretical estimate, no direct mapping
        'negative_affect': 'LOW',       # Theoretical estimate, no direct mapping
        'reward_sensitivity': 'LOW',    # Theoretical estimate from motivation literature
        'prediction_error_gain': 'LOW', # No direct measurement, theoretical value
        'exploration_rate': 'LOW',      # Theoretical estimate, no direct measurement
    },
    'asd_typical': {
        'base_rt': 'MODERATE',          # Happé & Frith (2006) - qualitative claim
        'rt_variability': 'MODERATE',   # Limited direct data on CV in ASD
        'rt_slowing': 'MODERATE',       # 10-15% claim needs verification
        'base_accuracy': 'MODERATE',    # Geurts et al. (2009) - flexibility data
        'accuracy_decline': 'LOW',      # Limited evidence for load effects
        'wm_capacity': 'MODERATE',      # Steele et al. (2007) - direct WM study
        'wm_decay_rate': 'LOW',         # Inferred from "manipulation impaired"
        'attention_stability': 'MODERATE', # Multiple studies show intact sustained attention
        'switch_cost': 'MODERATE',      # Yerys et al. (2009) + Geurts - direct evidence
        'vigilance_decrement': 'LOW',   # Rate not specified in sources
        'stress_baseline': 'HIGH',      # Corbett et al. (2009) - direct cortisol measurement
        'stress_reactivity': 'MODERATE',# Corbett et al. - elevated response observed
        'stress_recovery': 'MODERATE',  # Corbett et al. - prolonged elevation noted
        'positive_affect': 'LOW',       # Indirect inference from sensory reactivity
        'negative_affect': 'LOW',       # Indirect inference from sensory reactivity
        'reward_sensitivity': 'LOW',    # Limited evidence, theoretical estimate
        'prediction_error_gain': 'LOW', # No direct measurement
        'exploration_rate': 'LOW',      # Theoretical inference from reduced flexibility
    },
    'adhd_typical': {
        'base_rt': 'MODERATE',          # Klein et al. (2006) - slightly faster noted
        'rt_variability': 'HIGH',       # Kofler et al. (2013) META-ANALYSIS (319 studies!)
        'rt_slowing': 'MODERATE',       # Multiple studies show slight slowing
        'base_accuracy': 'HIGH',        # Kofler meta-analysis - omission errors quantified
        'accuracy_decline': 'MODERATE', # Multiple studies show load effects
        'wm_capacity': 'HIGH',          # Kasper et al. (2012) - meta-analysis
        'wm_decay_rate': 'LOW',         # Estimated from capacity deficit
        'attention_stability': 'HIGH',  # Huang-Pollock et al. (2012) - direct measurement
        'switch_cost': 'MODERATE',      # Lower cost from multiple studies (hyper-switching)
        'vigilance_decrement': 'MODERATE', # Huang-Pollock - strong evidence for steep decline
        'stress_baseline': 'MODERATE',  # Lackschewitz et al. (2008) - physiological data
        'stress_reactivity': 'MODERATE',# Lackschewitz et al. - high reactivity measured
        'stress_recovery': 'LOW',       # Impaired regulation noted, not quantified
        'positive_affect': 'LOW',       # Limited evidence, theoretical estimate
        'negative_affect': 'LOW',       # Limited evidence, theoretical estimate
        'reward_sensitivity': 'MODERATE', # Sonuga-Barke (2005) - delay aversion theory
        'prediction_error_gain': 'LOW', # Theoretical inference from impulsivity
        'exploration_rate': 'MODERATE', # Inferred from delay aversion + impulsivity
    },
    'mdd_typical': {
        'base_rt': 'MODERATE',          # Tsourtos et al. (2002) - psychomotor slowing
        'rt_variability': 'LOW',        # Limited data on CV in depression
        'rt_slowing': 'MODERATE',       # Tsourtos - 15-20% claim needs verification
        'base_accuracy': 'MODERATE',    # Porter et al. (2003) - drug-free patients
        'accuracy_decline': 'MODERATE', # Porter et al. - performance under load
        'wm_capacity': 'MODERATE',      # Christopher & MacDonald (2005) - direct WM study
        'wm_decay_rate': 'LOW',         # Estimated from load impairment
        'attention_stability': 'MODERATE', # Snyder (2013) - EF impairments review
        'switch_cost': 'MODERATE',      # Snyder (2013) - EF impairments noted
        'vigilance_decrement': 'LOW',   # Limited evidence, estimated
        'stress_baseline': 'HIGH',      # Burke et al. (2005) META-ANALYSIS (361 studies!)
        'stress_reactivity': 'MODERATE',# Burke et al. - HPA dysregulation documented
        'stress_recovery': 'MODERATE',  # Burke et al. - prolonged elevation
        'positive_affect': 'HIGH',      # Treadway & Zald (2011) - comprehensive anhedonia review
        'negative_affect': 'MODERATE',  # Multiple depression studies document elevated NA
        'reward_sensitivity': 'MODERATE', # Treadway & Zald - reduced reward processing
        'prediction_error_gain': 'LOW', # Theoretical inference from rumination
        'exploration_rate': 'LOW',      # Inferred from Nolen-Hoeksema rumination theory
    },
}


def get_preset(name: str) -> Dict[str, float]:
    """
    Get a clinical preset by name.
    
    Args:
        name: Preset name (e.g., 'neurotypical', 'asd_typical', 'adhd_typical', 'mdd_typical')
        
    Returns:
        Dictionary of preset parameters
        
    Raises:
        KeyError: If preset name not found
    """
    if name not in CLINICAL_PRESETS:
        available = ', '.join(list_presets())
        raise KeyError(f"Unknown preset '{name}'. Available: {available}")
    return CLINICAL_PRESETS[name].copy()


def list_presets() -> List[str]:
    """Return sorted list of available preset names."""
    return sorted(CLINICAL_PRESETS.keys())


def get_preset_description(name: str) -> str:
    """
    Get a human-readable description of a clinical preset.
    
    Args:
        name: Preset name
        
    Returns:
        Description string
    """
    descriptions = {
        'neurotypical': (
            "Neurotypical baseline: moderate RT (~500ms), high accuracy (~90%), "
            "normal working memory (4±1 items), adaptive stress response, flexible attention."
        ),
        'asd_typical': (
            "Autism Spectrum Disorder: 15% slower RT, heightened sensory reactivity, "
            "reduced attentional flexibility, elevated baseline stress, prolonged recovery."
        ),
        'adhd_typical': (
            "ADHD: 35-50% higher RT variability, 2-3x omission errors, reduced working memory (~3 items), "
            "poor sustained attention, impaired stress regulation, high impulsivity."
        ),
        'mdd_typical': (
            "Major Depressive Disorder: 20% psychomotor slowing, anhedonia (blunted positive affect), "
            "elevated stress/cortisol, impaired cognitive control, rumination."
        ),
    }
    return descriptions.get(name, f"No description available for '{name}'")


# =============================================================================
# REFERENCES (Clinical/Behavioral Literature Only)
# =============================================================================
#
# Neurotypical:
# 1. Ratcliff & McKoon (2008). The diffusion decision model: Theory and data for two-choice decision tasks
# 2. Cowan (2001). The magical number 4 in short-term memory: A reconsideration of mental storage capacity
# 3. McEwen (1998). Stress, adaptation, and disease: Allostasis and allostatic load
# 4. Posner & Petersen (1990). The attention system of the human brain
# 5. Luce, R. D. (1986). Response Times: Their Role in Inferring Elementary Mental Organization.
#    Oxford University Press. (Accuracy baselines: 85-95% typical for simple tasks)
#
# ASD:
# 6. Happé & Frith (2006). The weak coherence account: Detail-focused cognitive style in autism
# 7. Geurts, H. M., Corbett, B., & Solomon, M. (2009). The paradox of cognitive flexibility in autism.
#    Trends in Cognitive Sciences, 13(2), 74-82. (Set-shifting and flexibility deficits)
# 8. Steele, S. D., Minshew, N. J., Luna, B., & Sweeney, J. A. (2007). Spatial working memory deficits in autism.
#    Journal of Autism and Developmental Disorders, 37(4), 605-612.
# 9. Corbett, B. A., et al. (2009). Elevated cortisol during play is associated with stress in children with ASD
# 10. Yerys, B. E., et al. (2009). Set-shifting in children with ASD
# 11. Robertson & Baron-Cohen (2017). Sensory perception in autism
#
# ADHD:
# 12. Klein et al. (2006). Intra-subject variability in ADHD
# 13. Kofler et al. (2013). Reaction time variability in ADHD: A meta-analytic review
# 14. Kasper et al. (2012). Moderators of working memory deficits in ADHD
# 15. Huang-Pollock et al. (2012). Evaluating vigilance deficits in ADHD
# 16. Lackschewitz et al. (2008). Physiological and psychological stress responses in ADHD
# 17. Sonuga-Barke (2005). Causal models of ADHD: Delay aversion
#
# MDD:
# 18. Tsourtos et al. (2002). Evidence of information processing speed deficits in depression
# 19. Porter et al. (2003). Neurocognitive impairment in drug-free depression
# 20. Christopher & MacDonald (2005). The impact of clinical depression on working memory
# 21. Treadway & Zald (2011). Reconsidering anhedonia in depression
# 22. Burke et al. (2005). Depression and cortisol: A meta-analysis
# 23. Snyder (2013). Major depressive disorder is associated with broad impairments in executive function
# 24. Nolen-Hoeksema (2000). The role of rumination in depressive disorders
#
# =============================================================================


def get_parameter_confidence(preset: str, param: str) -> str:
    """
    Get confidence level for a specific parameter.
    
    Args:
        preset: Preset name (e.g., 'neurotypical', 'asd_typical')
        param: Parameter name (e.g., 'wm_capacity', 'stress_baseline')
        
    Returns:
        Confidence level: 'HIGH', 'MODERATE', 'LOW', or 'UNKNOWN'
        
    Examples:
        >>> get_parameter_confidence('adhd_typical', 'rt_variability')
        'HIGH'
        >>> get_parameter_confidence('neurotypical', 'exploration_rate')
        'LOW'
    """
    if preset not in PARAMETER_CONFIDENCE:
        return 'UNKNOWN'
    return PARAMETER_CONFIDENCE.get(preset, {}).get(param, 'UNKNOWN')


def get_preset_summary(preset: str) -> Dict[str, Dict[str, any]]:
    """
    Get preset parameters with confidence levels.
    
    Args:
        preset: Preset name
        
    Returns:
        Dictionary mapping parameter names to dicts with 'value' and 'confidence'
        
    Example:
        >>> summary = get_preset_summary('adhd_typical')
        >>> summary['wm_capacity']
        {'value': 3.0, 'confidence': 'HIGH'}
    """
    params = get_preset(preset)
    confidence = PARAMETER_CONFIDENCE.get(preset, {})
    return {
        param: {
            'value': value,
            'confidence': confidence.get(param, 'UNKNOWN')
        }
        for param, value in params.items()
    }
