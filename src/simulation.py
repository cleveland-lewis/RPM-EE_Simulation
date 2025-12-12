# RPM-EE Simulation Class (v1.1.0)

from sensory import SensoryInputSystem
from salience import SalienceTagger
from memory import MemoryStore
from rpm import RecursivePredictiveModeler
from emotion import EmotionalEncoder
from replay import ReplayModeArbitrator
from action import ActionSystem

class RPMEESimulation:
    def __init__(self):
        self.clock = 0
        self.logs = []

        # Initialize subsystems
        self.sensory = SensoryInputSystem()
        self.tagger = SalienceTagger()
        self.memory = MemoryStore()
        self.rpm = RecursivePredictiveModeler()
        self.encoder = EmotionalEncoder()
        self.arbitrator = ReplayModeArbitrator()
        self.action_system = ActionSystem()
        
        # System state tracking
        self.system_state = {
            "clock": 0,
            "state": "awake",
            "stress": 0.3,
            "prediction_error": 0.2,
            "emotion_volatility": 0.1
        }

    def step(self):
        # 1. Generate new input (sensory clock matches simulation clock)
        input_packet = self.sensory.generate_input()

        # 2. Tag sensory input with salience/emotion
        tagged_events = self.tagger.tag_input(input_packet)

        # 3. Store in memory and split matched vs unmatched
        self.memory.store_events(tagged_events)
        matched, unmatched = self.memory.match_patterns(tagged_events)

        # 4. Generate slot-based simulations
        simulations = self.rpm.generate_simulations(matched)

        # 5. Emotionally encode and adjust replay weight
        updated_simulations = self.encoder.encode_simulations(simulations)

        # 6. Select replay mode based on system state
        self.system_state["clock"] = self.clock
        self.system_state["state"] = input_packet["state"]
        replay_mode = self.arbitrator.select_mode(self.system_state)

        # 7. Select and execute action
        action = self.action_system.select_action(
            updated_simulations, 
            replay_mode, 
            self.system_state
        )
        action_outcome = self.action_system.execute_action(action, self.system_state)
        
        # 8. Update system state based on action outcome
        self._update_system_state(action_outcome, tagged_events)

        # 9. Log step results
        self.logs.append({
            "clock": self.clock,
            "state": input_packet["state"],
            "num_events": len(tagged_events),
            "num_matched": len(matched),
            "num_unmatched": len(unmatched),
            "num_simulations": len(updated_simulations),
            "replay_mode": replay_mode,
            "action": action.get("type"),
            "action_success": action_outcome.get("success"),
            "stress": round(self.system_state["stress"], 3),
            "prediction_error": round(self.system_state["prediction_error"], 3)
        })
    
    def _update_system_state(self, action_outcome, events):
        """Update system state based on action outcomes and events."""
        # Apply action outcome deltas
        state_change = action_outcome.get("state_change", {})
        self.system_state["stress"] += state_change.get("stress_delta", 0)
        self.system_state["prediction_error"] += state_change.get("prediction_error_delta", 0)
        self.system_state["emotion_volatility"] += state_change.get("emotion_volatility_delta", 0)
        
        # Calculate emotion volatility from events
        if events:
            valences = [e.get("emotion", {}).get("valence", 0) for e in events]
            if len(valences) > 1:
                volatility = max(valences) - min(valences)
                self.system_state["emotion_volatility"] = 0.7 * self.system_state["emotion_volatility"] + 0.3 * volatility
        
        # Clamp values to valid ranges
        self.system_state["stress"] = max(0, min(1.0, self.system_state["stress"]))
        self.system_state["prediction_error"] = max(0, min(1.0, self.system_state["prediction_error"]))
        self.system_state["emotion_volatility"] = max(0, min(1.0, self.system_state["emotion_volatility"]))
        
        # Natural decay towards baseline
        self.system_state["stress"] *= 0.98
        self.system_state["prediction_error"] *= 0.95
        self.system_state["emotion_volatility"] *= 0.90

    def run(self, episodes=100):
        for episode in range(episodes):
            self.clock += 1
            # Sync sensory clock with simulation clock
            self.sensory.clock = self.clock
            # Update sensory state based on timer
            self.sensory.state_timer -= 1
            if self.sensory.state_timer <= 0:
                self.sensory.transition_state()
            
            self.step()
            if episode % 10 == 0:
                print(f"Episode {episode} complete")

        print("Simulation complete.")