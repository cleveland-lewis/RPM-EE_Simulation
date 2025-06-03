# src/sensory.py
import random

class SensoryInputSystem:
    def __init__(self):
        self.clock = 0
        self.state = "awake"
        self.state_durations = {
            "awake": 10,
            "fatigued": 5,
            "asleep": 8
        }
        self.state_timer = self.state_durations[self.state]

    def transition_state(self):
        if self.state == "awake":
            self.state = "fatigued"
        elif self.state == "fatigued":
            self.state = "asleep"
        elif self.state == "asleep":
            self.state = "awake"
        self.state_timer = self.state_durations[self.state]

    def update_clock(self):
        self.clock += 1
        self.state_timer -= 1
        if self.state_timer <= 0:
            self.transition_state()

    def _awake_cycle(self):
        modalities = ["vision", "hearing", "touch", "smell", "taste"]
        events = {}
        for mod in modalities:
            count = random.randint(1, 3)
            events[mod] = []
            for _ in range(count):
                event = {
                    "modality": mod,
                    "intensity": random.uniform(0.1, 1.0),
                    "duration": random.randint(1, 5)
                }
                events[mod].append(event)
        return events

    def _sleep_cycle(self):
        # Only hearing and touch have exactly one event each during sleep
        events = {
            "vision": [],
            "hearing": [{
                "modality": "hearing",
                "intensity": random.uniform(0.1, 0.5),
                "duration": random.randint(1, 3)
            }],
            "touch": [{
                "modality": "touch",
                "intensity": random.uniform(0.1, 0.5),
                "duration": random.randint(1, 3)
            }],
            "smell": [],
            "taste": []
        }
        return events

    def generate_input(self):
        if self.state == "awake":
            events = self._awake_cycle()
        elif self.state == "asleep":
            events = self._sleep_cycle()
        else:
            # fatigued state: can be implemented similarly if needed
            events = {
                "vision": [],
                "hearing": [],
                "touch": [],
                "smell": [],
                "taste": []
            }

        packet = {
            "clock": self.clock,
            "state": self.state,
            "vision": events.get("vision", []),
            "hearing": events.get("hearing", []),
            "touch": events.get("touch", []),
            "smell": events.get("smell", []),
            "taste": events.get("taste", [])
        }
        return packet