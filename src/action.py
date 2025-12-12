# RPM-EE Action System (v1.1.0)

import random

class ActionSystem:
    """
    Selects and executes actions based on simulations and replay mode.
    Provides feedback to the sensory system.
    """
    
    # Constants for action execution
    MIN_SUCCESS_PROB = 0.1  # Minimum success probability
    CONFIDENCE_MULTIPLIER = 0.8  # How much confidence affects success probability
    
    def __init__(self):
        self.action_history = []
        self.available_actions = [
            "approach", "withdraw", "explore", "recoil", "observe", 
            "rest", "express", "suppress"
        ]
        
    def select_action(self, simulations, replay_mode, system_state):
        """
        Select an action based on:
        - Available simulations with replay weights
        - Current replay mode (problem_solving, soothing, pattern_search, rest)
        - System state (stress, emotion, etc.)
        
        Returns:
            Dict with action details
        """
        if not simulations:
            # No simulations, default action
            return self._default_action(system_state)
        
        # Filter and weight simulations based on mode
        weighted_sims = self._apply_mode_filter(simulations, replay_mode)
        
        if not weighted_sims:
            return self._default_action(system_state)
        
        # Select simulation based on replay_weight
        selected_sim = self._weighted_selection(weighted_sims)
        
        # Extract action from simulation
        action = {
            "type": selected_sim.get("action", "observe"),
            "source_simulation_id": selected_sim.get("id"),
            "confidence": selected_sim.get("plausibility", 0.5),
            "emotional_valence": selected_sim.get("emotion", {}).get("valence", 0),
            "mode": replay_mode
        }
        
        self.action_history.append(action)
        return action
    
    def execute_action(self, action, current_state):
        """
        Simulate action execution and generate result.
        
        Returns:
            Dict with action outcome (success, impact, feedback)
        """
        action_type = action.get("type", "observe")
        confidence = action.get("confidence", 0.5)
        
        # Simulate success probability based on confidence
        success_prob = confidence * self.CONFIDENCE_MULTIPLIER + self.MIN_SUCCESS_PROB
        success = random.random() < success_prob
        
        # Generate outcome feedback
        outcome = {
            "action": action_type,
            "success": success,
            "impact": self._calculate_impact(action, success),
            "feedback_valence": random.gauss(0.5 if success else -0.5, 0.2),
            "state_change": self._calculate_state_change(action, success, current_state)
        }
        
        return outcome
    
    def _apply_mode_filter(self, simulations, mode):
        """Filter simulations based on replay mode."""
        filtered = []
        
        for sim in simulations:
            weight = sim.get("replay_weight", 1.0)
            emotion_val = sim.get("emotion", {}).get("valence", 0)
            
            # Adjust weight based on mode
            if mode == "soothing":
                # Prefer positive emotions
                if emotion_val > 0:
                    weight *= 1.5
                else:
                    weight *= 0.5
                    
            elif mode == "problem_solving":
                # Prefer high plausibility
                plausibility = sim.get("plausibility", 0.5)
                weight *= (1 + plausibility)
                
            elif mode == "pattern_search":
                # Prefer novel patterns (low fatigue)
                if not sim.get("fatigue_flag", False):
                    weight *= 1.3
                    
            elif mode == "rest":
                # Prefer low emotion intensity
                emotion_intensity = abs(emotion_val)
                weight *= (1 - emotion_intensity * 0.5)
            
            filtered.append({**sim, "adjusted_weight": weight})
        
        return filtered
    
    def _weighted_selection(self, weighted_sims):
        """Select a simulation using weighted random selection."""
        total_weight = sum(s.get("adjusted_weight", 1.0) for s in weighted_sims)
        
        if total_weight <= 0:
            return random.choice(weighted_sims)
        
        r = random.uniform(0, total_weight)
        cumulative = 0
        
        for sim in weighted_sims:
            cumulative += sim.get("adjusted_weight", 1.0)
            if cumulative >= r:
                return sim
        
        return weighted_sims[-1]  # Fallback
    
    def _default_action(self, system_state):
        """Generate default action when no simulations available."""
        state = system_state.get("state", "awake")
        
        if state == "asleep":
            action_type = "rest"
        elif state == "fatigued":
            action_type = random.choice(["rest", "observe"])
        else:
            action_type = "observe"
        
        return {
            "type": action_type,
            "source_simulation_id": None,
            "confidence": 0.3,
            "emotional_valence": 0,
            "mode": "default"
        }
    
    def _calculate_impact(self, action, success):
        """Calculate impact magnitude of action."""
        base_impact = 0.5
        
        if success:
            impact = base_impact + random.uniform(0.2, 0.4)
        else:
            impact = base_impact - random.uniform(0.1, 0.3)
        
        return max(0, min(1.0, impact))
    
    def _calculate_state_change(self, action, success, current_state):
        """Calculate how action changes system state."""
        # Simple state change simulation
        state_change = {
            "stress_delta": 0,
            "prediction_error_delta": 0,
            "emotion_volatility_delta": 0
        }
        
        if success:
            state_change["stress_delta"] = -0.1
            state_change["prediction_error_delta"] = -0.05
        else:
            state_change["stress_delta"] = 0.1
            state_change["prediction_error_delta"] = 0.1
            state_change["emotion_volatility_delta"] = 0.05
        
        return state_change
