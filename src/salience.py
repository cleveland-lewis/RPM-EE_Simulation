import math
import random
import uuid
from datetime import datetime


class SalienceTagger:
    MODALITIES = ["vision", "hearing", "touch", "smell", "taste"]

    def __init__(self, salience_decay=0.01, weight_error_corr=1.0, weight_soothing=1.0,
                 timing_center=300, timing_steepness=0.1):
        self.salience_decay = salience_decay
        self.weight_error_corr = weight_error_corr
        self.weight_soothing = weight_soothing
        self.timing_center = timing_center
        self.timing_steepness = timing_steepness

        # Track recurrence of event types per modality
        self.recurrence_memory = {}

    def tag_input(self, input_packet, debug=False):
        tagged_events = []

        # Precompute shared weight for other factors
        rem = 1.0 - (self.weight_error_corr + self.weight_soothing)
        other_w = rem / 5.0

        for modality in self.MODALITIES:
            for event in input_packet[modality]:
                tagged = self._tag_event(
                    event, modality,
                    input_packet["clock"],
                    input_packet["state"],
                    other_w,
                    debug
                )
                tagged_events.append(tagged)
        return tagged_events

    def _tag_event(self, event, modality, clock, state, other_w, debug=False):
        novelty = random.uniform(0.2, 1.0)
        emotion = self._simulate_emotion(modality, event["intensity"])

        # Recurrence tracking (requires event["type"] field)
        event_key = (modality, event.get("type", "unknown"))
        self.recurrence_memory[event_key] = self.recurrence_memory.get(event_key, 0) + 1
        recurrence = 1.0 / self.recurrence_memory[event_key]  # Decreases over time

        # Timing salience with parametrized sigmoid
        raw_timing = 1.0 / (1.0 + math.exp(-self.timing_steepness * (clock - self.timing_center)))
        timing = raw_timing * (1.0 - self.salience_decay)

        duration = event["duration"]
        intensity = event["intensity"]

        prioritization_score = (
            novelty * other_w +
            emotion["valence"] * self.weight_soothing +
            recurrence * self.weight_error_corr +
            timing * other_w +
            duration * other_w +
            intensity * other_w
        )

        if debug:
            print(f"[DEBUG] Modality: {modality}")
            print(f"  Event Key: {event_key}")
            print(f"  Novelty: {novelty:.4f}")
            print(f"  Emotion: {emotion}")
            print(f"  Recurrence Count: {self.recurrence_memory[event_key]}")
            print(f"  Timing: {timing:.4f}")
            print(f"  Duration: {duration}")
            print(f"  Intensity: {intensity}")
            print(f"  Prioritization Score: {prioritization_score:.4f}")

        return {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "modality": modality,
            "state": state,
            "novelty": round(novelty, 4),
            "emotion": emotion,
            "recurrence": round(recurrence, 4),
            "timing": round(timing, 4),
            "duration": duration,
            "intensity": intensity,
            "prioritization_score": round(prioritization_score, 4)
        }

    def _simulate_emotion(self, modality, intensity):
        # Sigmoid scaling for smooth gradation
        sigmoid_valence = 2 / (1 + math.exp(-10 * (intensity - 0.5))) - 1

        # Modality-specific emotional bias
        modality_bias = {
            "vision": 0.4,
            "hearing": 0.2,
            "touch": -0.3,
            "smell": -0.5,
            "taste": 0.6
        }

        valence = sigmoid_valence + modality_bias.get(modality, 0.0)
        valence = max(-1.0, min(1.0, round(valence, 3)))  # Clamp to [-1, 1]

        # Optional: valence bins to assign category
        category = "neutral"
        if valence > 0.6:
            category = "high_positive"
        elif valence > 0.2:
            category = "positive"
        elif valence < -0.6:
            category = "high_negative"
        elif valence < -0.2:
            category = "negative"

        return {"valence": valence, "category": category}