# RPM-EE Simulation Class (v1.1.0 Integrated)

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

class RPMEESimulation:
    def __init__(self):
        self.clock = 0
        self.logs = []

        # Subsystems
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

        # Example system state for mode selection
        system_state = {
            "clock": self.clock,
            "stress": self.self_model.schema_stress,
            "prediction_error": sum(sim.get("schema_mismatch", 0.0) for sim in evaluated) / max(1, len(evaluated)),
            "emotion_volatility": sum(abs(sim["emotional_prediction"]) for sim in evaluated) / max(1, len(evaluated))
        }

        mode = self.replay_mode.select_mode(system_state)

        # Log basic metrics
        self.logs.append({
            "clock": self.clock,
            "state": input_packet["state"],
            "replay_mode": mode,
            "num_tagged": len(tagged_events),
            "num_simulations": len(simulations),
            "attunement_score": attunement_score,
            "schema_stress": round(self.self_model.schema_stress, 3)
        })

    def run(self, episodes=100):
        for episode in range(episodes):
            self.clock += 1
            self.step()
            if episode % 10 == 0:
                print(f"Episode {episode} complete")
        print("Simulation complete.")
