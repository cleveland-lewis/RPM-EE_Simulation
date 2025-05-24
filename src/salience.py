import uuid
import random
import math
from datetime import datetime

class SalienceTagger:
    def __init__(self):
        self.memory_id_counter = 0

    def tag_input(self, input_packet):
        tagged_events = []
        for modality in ["vision", "hearing", "touch", "smell", "taste"]:
            for event in input_packet[modality]:
                tagged = self._tag_event(event, modality, input_packet["clock"], input_packet["state"])
                tagged_events.append(tagged)
        return tagged_events

    def _tag_event(self, event, modality, clock, state):
        novelty = random.uniform(0.2, 1.0)  # Placeholder: will later compare to memory store
        emotion = self._simulate_emotion(modality, event["intensity"])
        recurrence = 0  # Placeholder for future schema integration
        timing = 1.0 / (1.0 + math.exp(-0.1 * (clock - 300)))  # Soft curve for recency
        duration = event["duration"]
        intensity = event["intensity"]

        prioritization_score = (
            0.25 * novelty +
            0.25 * emotion["valence"] +
            0.1 * recurrence +
            0.15 * timing +
            0.15 * duration +
            0.1 * intensity
        )

        return {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "modality": modality,
            "state": state,
            "novelty": novelty,
            "emotion": emotion,
            "recurrence": recurrence,
            "timing": timing,
            "duration": duration,
            "intensity": intensity,
            "prioritization_score": round(prioritization_score, 4)
        }

    def _simulate_emotion(self, modality, intensity):
        # Placeholder: real implementation will depend on affective modeling
        valence = 0.0
        category = "neutral"

        if modality == "vision" and intensity > 0.7:
            valence = 0.8
            category = "awe"
        elif modality == "hearing" and intensity > 0.6:
            valence = 0.6
            category = "surprise"
        elif modality == "touch" and intensity > 0.5:
            valence = -0.4
            category = "discomfort"
        elif modality == "smell" and intensity > 0.5:
            valence = -0.6
            category = "disgust"
        elif modality == "taste" and intensity > 0.5:
            valence = 0.7
            category = "pleasure"

        return {"valence": valence, "category": category}
