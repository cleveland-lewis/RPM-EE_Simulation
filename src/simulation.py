# RPM-EE Simulation Class (v1.1.0 Integrated with Clinical Presets)

try:
    # Try relative imports first (when used as package)
    from .sensory import SensoryInputSystem
    from .salience import SalienceTagger
    from .memory import MemoryStore
    from .rpm import RecursivePredictiveModeler
    from .emotion import EmotionalEncoder
    from .replay import ReplayModeArbitrator
    from .fatigue import ReplayFatigueSuppressor
    from .arbiter import SimulationClusterArbiter
    from .selfmodel import SelfModel
    from .attunement import SocialAttunementSystem
    from .presets import get_preset
except ImportError:
    # Fall back to absolute imports (when run directly)
    from sensory import SensoryInputSystem
    from salience import SalienceTagger
    from memory import MemoryStore
    from rpm import RecursivePredictiveModeler
    from emotion import EmotionalEncoder
    from replay import ReplayModeArbitrator
    from fatigue import ReplayFatigueSuppressor
    from arbiter import SimulationClusterArbiter
    from selfmodel import SelfModel
    from attunement import SocialAttunementSystem
    from presets import get_preset

class RPMEESimulation:
    def __init__(self, preset='neurotypical'):
        """
        Initialize simulation with clinical preset.
        
        Args:
            preset: Clinical preset name (default: 'neurotypical')
                   Options: 'neurotypical', 'asd_typical', 'adhd_typical', 'mdd_typical'
        """
        self.clock = 0
        self.logs = []
        
        # Load clinical preset parameters
        self.preset_name = preset
        self.params = get_preset(preset)

        # Subsystems (initialized with preset parameters)
        self.sensory = SensoryInputSystem()
        self.tagger = SalienceTagger()
        self.memory = MemoryStore()
        self.rpm = RecursivePredictiveModeler()
        self.encoder = EmotionalEncoder()
        self.replay_mode = ReplayModeArbitrator()
        self.fatigue = ReplayFatigueSuppressor()
        self.arbiter = SimulationClusterArbiter()
        self.self_model = SelfModel()
        self.attuner = SocialAttunementSystem()
        
        # Apply clinical preset to subsystems
        self._configure_from_preset()

    def _configure_from_preset(self):
        """Apply clinical preset parameters to subsystems."""
        # Configure self model with stress parameters
        self.self_model.schema_stress = self.params['stress_baseline']
        self.stress_reactivity = self.params['stress_reactivity']
        self.stress_recovery = self.params['stress_recovery']
        
        # Configure memory with WM capacity
        self.memory.capacity = int(self.params['wm_capacity'])
        self.memory.decay_rate = self.params['wm_decay_rate']
        
        # Configure emotional baseline
        self.self_model.emotion_baseline = (
            self.params['positive_affect'] - self.params['negative_affect']
        )
        
        # Store attention/executive parameters
        self.attention_stability = self.params['attention_stability']
        self.switch_cost = self.params['switch_cost']
        self.vigilance_decrement = self.params['vigilance_decrement']
        
        # Store prediction/learning parameters
        self.prediction_error_gain = self.params['prediction_error_gain']
        self.exploration_rate = self.params['exploration_rate']

    def step(self):
        self.sensory.update_clock()
        input_packet = self.sensory.generate_input()
        tagged_events = self.tagger.tag_input(input_packet)
        self.memory.store_events(tagged_events)
        matched, unmatched = self.memory.match_patterns(tagged_events)
        simulations = self.rpm.generate_simulations(matched)
        encoded = self.encoder.encode_simulations(simulations)
        fatigued = self.fatigue.apply_fatigue(encoded)
        scored = self.arbiter.score_simulations(fatigued)
        ranked = self.arbiter.sort_simulations(scored)
        evaluated = self.self_model.evaluate_simulations(ranked)
        attunement_score = self.attuner.evaluate_predictions(evaluated)

        # Example system state for mode selection (with clinical parameters)
        system_state = {
            "clock": self.clock,
            "stress": self.self_model.schema_stress,
            "prediction_error": sum(sim.get("schema_mismatch", 0.0) for sim in evaluated) / max(1, len(evaluated)),
            "emotion_volatility": sum(abs(sim["emotional_prediction"]) for sim in evaluated) / max(1, len(evaluated)),
            "attention_stability": self.attention_stability,
            "vigilance_level": max(0.0, self.attention_stability - self.vigilance_decrement * self.clock / 100)
        }

        mode = self.replay_mode.select_mode(system_state)
        
        # Apply stress dynamics based on clinical preset
        self._update_stress(system_state)

        # Log basic metrics with clinical parameters
        self.logs.append({
            "clock": self.clock,
            "state": input_packet["state"],
            "replay_mode": mode,
            "num_tagged": len(tagged_events),
            "num_simulations": len(simulations),
            "attunement_score": attunement_score,
            "schema_stress": round(self.self_model.schema_stress, 3),
            "preset": self.preset_name,
            "vigilance": round(system_state["vigilance_level"], 3)
        })
    
    def _update_stress(self, system_state):
        """Update stress based on clinical preset parameters."""
        # Stress increases with prediction errors (reactivity)
        pe = system_state["prediction_error"]
        if pe > 0.5:
            self.self_model.schema_stress += self.stress_reactivity * pe * 0.1
        
        # Stress recovery (decay) based on preset
        self.self_model.schema_stress *= (1.0 - self.stress_recovery)
        
        # Clamp stress to [0, 1]
        self.self_model.schema_stress = max(0.0, min(1.0, self.self_model.schema_stress))

    def run(self, episodes=100):
        for episode in range(episodes):
            self.clock += 1
            self.step()
            if episode % 10 == 0:
                print(f"Episode {episode} complete")
        print("Simulation complete.")
