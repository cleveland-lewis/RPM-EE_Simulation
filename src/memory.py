import uuid
from collections import deque
import math

class MemoryStore:
    def __init__(self, max_short_term=1000):
        self.short_term = deque(maxlen=max_short_term)
        self.long_term = {}
        # Clinical preset parameters (can be updated)
        self.capacity = 7  # Default WM capacity (7±2)
        self.decay_rate = 0.01  # Default decay rate

    def store_events(self, tagged_events):
        for event in tagged_events:
            self.short_term.append(event)
        # Apply memory decay based on clinical preset
        self._apply_decay()
    
    def _apply_decay(self):
        """Apply decay to memory items based on clinical preset decay rate."""
        for event in self.short_term:
            if 'prioritization_score' in event:
                event['prioritization_score'] *= (1.0 - self.decay_rate)
    
    def get_working_memory_load(self):
        """Calculate working memory load based on capacity."""
        active_items = sum(1 for e in self.short_term if e.get('prioritization_score', 0) > 0.5)
        return min(1.0, active_items / self.capacity) if self.capacity > 0 else 0.0

    def match_patterns(self, new_events):
        matched = []
        unmatched = []
        for event in new_events:
            similarity_score = self._compare_to_memory(event)
            if similarity_score > 0.8:
                matched.append(event)
                event["recurrence"] = 1  # simple bump, could be a running average
            else:
                unmatched.append(event)
        return matched, unmatched

    def _compare_to_memory(self, event):
        # Simplified cosine-like comparison with existing short-term memory
        if not self.short_term:
            return 0.0
        scores = []
        for past_event in self.short_term:
            sim = self._event_similarity(event, past_event)
            scores.append(sim)
        return max(scores) if scores else 0.0

    def _event_similarity(self, e1, e2):
        weights = {
            "modality": 0.1,
            "duration": 0.1,
            "intensity": 0.1,
            "emotion_valence": 0.3,
            "timing": 0.2,
            "prioritization_score": 0.2
        }

        sim = 0
        sim += weights["modality"] * (1.0 if e1["modality"] == e2["modality"] else 0.0)
        sim += weights["duration"] * (1.0 - abs(e1["duration"] - e2["duration"]) / 10.0)
        sim += weights["intensity"] * (1.0 - abs(e1["intensity"] - e2["intensity"]))
        sim += weights["emotion_valence"] * (1.0 - abs(e1["emotion"]["valence"] - e2["emotion"]["valence"]))
        sim += weights["timing"] * (1.0 - abs(e1["timing"] - e2["timing"]))
        sim += weights["prioritization_score"] * (1.0 - abs(e1["prioritization_score"] - e2["prioritization_score"]) / 10.0)
        return max(0.0, min(1.0, sim))  # clamp between 0 and 1

    def prune_old_memory(self):
        self.short_term = deque([e for e in self.short_term if e["prioritization_score"] > 0.3], maxlen=self.short_term.maxlen)
