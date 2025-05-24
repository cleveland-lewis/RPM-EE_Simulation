# Create the SensoryInputSystem module inside the simulation package

sensory_input_code = """\
import random

class SensoryInputSystem:
    def __init__(self):
        self.clock = 0
        self.state = "awake"  # can be: awake, fatigued, asleep
        self.state_durations = {"awake": 300, "fatigued": 100, "asleep": 100}
        self.state_timer = self.state_durations[self.state]

    def update_clock(self):
        self.clock += 1
        self.state_timer -= 1
        if self.state_timer <= 0:
            self.transition_state()

    def transition_state(self):
        if self.state == "awake":
            self.state = "fatigued"
        elif self.state == "fatigued":
            self.state = "asleep"
        elif self.state == "asleep":
            self.state = "awake"
        self.state_timer = self.state_durations[self.state]

    def generate_input(self):
        # Simulate input channels: vision, hearing, touch, smell, taste
        # Each input is a list of features tagged with modality, intensity, duration
        input_packet = {
            "clock": self.clock,
            "state": self.state,
            "vision": self._simulate_vision(),
            "hearing": self._simulate_hearing(),
            "touch": self._simulate_touch(),
            "smell": self._simulate_smell(),
            "taste": self._simulate_taste()
        }
        return input_packet

    def _simulate_vision(self):
        if self.state == "asleep":
            return []
        return [{"modality": "vision", "intensity": random.uniform(0.1, 1.0), "duration": random.randint(1, 10)} for _ in range(random.randint(0, 3))]

    def _simulate_hearing(self):
        if self.state == "asleep":
            return [{"modality": "hearing", "intensity": random.uniform(0.0, 0.3), "duration": random.randint(1, 5)}]
        return [{"modality": "hearing", "intensity": random.uniform(0.2, 1.0), "duration": random.randint(1, 10)} for _ in range(random.randint(0, 2))]

    def _simulate_touch(self):
        if self.state == "asleep":
            return [{"modality": "touch", "intensity": random.uniform(0.0, 0.2), "duration": 1}]
        return [{"modality": "touch", "intensity": random.uniform(0.3, 1.0), "duration": random.randint(1, 4)} for _ in range(random.randint(1, 2))]

    def _simulate_smell(self):
        return [{"modality": "smell", "intensity": random.uniform(0.0, 0.6), "duration": 3}] if random.random() < 0.3 else []

    def _simulate_taste(self):
        return [{"modality": "taste", "intensity": random.uniform(0.1, 0.7), "duration": 2}] if random.random() < 0.1 else []

"""