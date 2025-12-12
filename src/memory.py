# RPM-EE Memory Store (v1.1.0)

import uuid
from collections import deque
import math

class MemoryStore:
    def __init__(self, max_short_term=1000):
        self.short_term = deque(maxlen=max_short_term)
        self.long_term = {}

    def store_events(self, tagged_events):
        for event in tagged_events:
            self.short_term.append(event)

    def match_patterns(self, new_events):
        matched = []
        unmatched = []
        for event in new_events:
            similarity_score = self._compare_to_memory(event)
            if similarity_score > 0.8:
                matched.append(event)
                event["recurrence"] = event.get("recurrence", 0) + 1  # simple bump, could be a running average
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
        sim += weights["modality"] * (1.0 if e1.get("modality") == e2.get("modality") else 0.0)
        sim += weights["duration"] * (1.0 - min(abs(e1.get("duration", 0) - e2.get("duration", 0)) / 10.0, 1.0))
        sim += weights["intensity"] * (1.0 - min(abs(e1.get("intensity", 0) - e2.get("intensity", 0)), 1.0))
        
        # Safe access to nested emotion dict
        e1_valence = e1.get("emotion", {}).get("valence", 0)
        e2_valence = e2.get("emotion", {}).get("valence", 0)
        sim += weights["emotion_valence"] * (1.0 - min(abs(e1_valence - e2_valence), 1.0))
        
        sim += weights["timing"] * (1.0 - min(abs(e1.get("timing", 0) - e2.get("timing", 0)), 1.0))
        sim += weights["prioritization_score"] * (1.0 - min(abs(e1.get("prioritization_score", 0) - e2.get("prioritization_score", 0)) / 10.0, 1.0))
        return max(0.0, min(1.0, sim))  # clamp between 0 and 1

    def prune_old_memory(self):
        self.short_term = deque([e for e in self.short_term if e.get("prioritization_score", 0) > 0.3], maxlen=self.short_term.maxlen)