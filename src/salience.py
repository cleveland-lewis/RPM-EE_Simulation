import math
import random
import uuid
from datetime import datetime


class SalienceTagger:
    def __init__(self, salience_decay=0.01, weight_error_corr=1.0, weight_soothing=1.0):
        self.memory_id_counter = 0
        self.salience_decay = salience_decay
        self.weight_error_corr = weight_error_corr
        self.weight_soothing = weight_soothing

    def tag_input(self, input_packet):
        tagged_events = []
        for modality in ["vision", "hearing", "touch", "smell", "taste"]:
            for event in input_packet[modality]:
                tagged = self._tag_event(event, modality,
                                         input_packet["clock"],
                                         input_packet["state"])
                tagged_events.append(tagged)
        return tagged_events

    def _tag_event(self, event, modality, clock, state):
        # Feature‐values
        novelty = random.uniform(0.2, 1.0)
        emotion = self._simulate_emotion(modality, event["intensity"])
        recurrence = 0.0
        # apply decay to timing score
        raw_timing = 1.0 / (1.0 + math.exp(-0.1 * (clock - 300)))
        timing = raw_timing * (1.0 - self.salience_decay)
        duration = event["duration"]
        intensity = event["intensity"]

        # Distribute remaining weight equally
        rem = 1.0 - (self.weight_error_corr + self.weight_soothing)
        other_w = rem / 5.0

        prioritization_score = (
                novelty * other_w +
                emotion["valence"] * self.weight_soothing +
                recurrence * self.weight_error_corr +
                timing * other_w +
                duration * other_w +
                intensity * other_w
        )

        return {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "modality": modality,
            "state": state,
            "novelty": round(novelty, 4),
            "emotion": emotion,
            "recurrence": recurrence,
            "timing": round(timing, 4),
            "duration": duration,
            "intensity": intensity,
            "prioritization_score": round(prioritization_score, 4)
        }

    def _simulate_emotion(self, modality, intensity):
        valence = 0.0
        category = "neutral"
        if modality == "vision" and intensity > 0.7:
            valence, category = 0.8, "awe"
        elif modality == "hearing" and intensity > 0.6:
            valence, category = 0.6, "surprise"
        elif modality == "touch" and intensity > 0.5:
            valence, category = -0.4, "discomfort"
        elif modality == "smell" and intensity > 0.5:
            valence, category = -0.6, "disgust"
        elif modality == "taste" and intensity > 0.5:
            valence, category = 0.7, "pleasure"
        return {"valence": valence, "category": category}
