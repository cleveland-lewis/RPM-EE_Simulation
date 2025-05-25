from arbiter import SimulationClusterArbiter
from attunement import SocialAttunementSystem
from emotion import EmotionalEncoder
from fatigue import ReplayFatigueSuppressor
from memory import MemoryStore
from replay import ReplayModeArbitrator
from rpm import RecursivePredictiveModeler
from salience import SalienceTagger
from selfmodel import SelfModel
from sensory import SensoryInputSystem


class RPMEESimulation:
    """
    Orchestrates the RPM-EE simulation by coordinating subsystems across time steps.
    Tracks internal states including attunement, schema stress, and replay dynamics.
    """

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

        prediction_error = sum(sim.get("schema_mismatch", 0.0) for sim in evaluated) / max(1, len(evaluated))
        emotion_volatility = sum(abs(sim.get("emotional_prediction", 0.0)) for sim in evaluated) / max(1,
                                                                                                       len(evaluated))

        # Example system state for mode selection
        system_state = {
            "clock": self.clock,
            "stress": self.self_model.schema_stress,
            "prediction_error": prediction_error,
            "emotion_volatility": emotion_volatility
        }

        mode = self.replay_mode.select_mode(system_state)

        # Log basic metrics
        self.logs.append({
            "clock": self.clock,
            "state": input_packet.get("state", None),
            "replay_mode": mode,
            "num_tagged": len(tagged_events),
            "num_simulations": len(simulations),
            "attunement_score": round(attunement_score, 3),
            "schema_stress": round(self.self_model.schema_stress, 3)
        })

    def run(self, episodes=100):
        """
        Run the simulation for a defined number of episodes.

        Args:
            episodes (int): Number of simulation steps to execute.
        """
        for episode in range(episodes):
            self.clock += 1
            self.step()
            if episode % 10 == 0:
                print(f"Episode {episode} complete")
        print("Simulation complete.")
