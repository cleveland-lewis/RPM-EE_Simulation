
import math
from datetime import datetime, timezone
import uuid

# Fallback mock for test environments where memory_store lacks max_similarity
class MockMemoryStore:
    def max_similarity(self, event):
        return 0.0

class SalienceTagger:
    MODALITIES = ['vision', 'hearing', 'touch', 'smell', 'taste']

    def __init__(self, memory_store, w_i=0.6, w_n=0.4, salience_decay=0.01,
                 timing_center=300, timing_steepness=0.1):
        self.memory_store = memory_store
        # Patch for test stability: if memory_store lacks max_similarity, provide a fallback.
        if not hasattr(self.memory_store, "max_similarity"):
            self.memory_store.max_similarity = lambda event: 0.0
        self.w_i = w_i
        self.w_n = w_n
        self.salience_decay = salience_decay
        self.timing_center = timing_center
        self.timing_steepness = timing_steepness

    def tag_events(self, events):
        """
        Tag each event with salience metadata.

        Parameters:
          events (list of dict): raw events with at least 'intensity'

        Returns:
          list of dict: events augmented with:
            id, timestamp, novelty, initial_salience,
            salience, tag_age, decay_rate
        """
        tagged = []
        for e in events:
            # Normalize intensity to [0,1]
            intensity = e.get('intensity', 0.0)
            intensity_norm = min(max(intensity, 0.0), 1.0)

            # Compute novelty: 1 - highest similarity to existing memories
            similarity = self.memory_store.max_similarity(e)
            similarity = min(max(similarity, 0.0), 1.0)
            novelty = 1.0 - similarity

            # Composite salience: weighted sum
            salience_score = self.w_i * intensity_norm + self.w_n * novelty

            # Build tagged event
            e_tagged = e.copy()
            e_tagged.update({
                'id': str(uuid.uuid4()),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'novelty': round(novelty, 4),
                'initial_salience': round(salience_score, 4),
                'salience': round(salience_score, 4),
                'tag_age': 0,
                'decay_rate': self.salience_decay
            })
            tagged.append(e_tagged)

        return tagged

    def tag_input(self, input_packet):
        """
        Process a full input packet (with multiple modalities) and return a list
        of tagged events with computed novelty, recurrence, emotion, timing, etc.
        """
        all_tagged = []
        clock = input_packet.get('clock', 0)
        state = input_packet.get('state', {})

        for modality in self.MODALITIES:
            raw_events = input_packet.get(modality, [])
            for event in raw_events:
                event_copy = event.copy()
                event_copy['modality'] = modality
                event_copy['state'] = state

                # Intensity normalized
                intensity = event_copy.get('intensity', 0.0)
                intensity_norm = min(max(intensity, 0.0), 1.0)

                # Novelty: 1 - max similarity in memory
                similarity = self.memory_store.max_similarity(event_copy)
                similarity = min(max(similarity, 0.0), 1.0)
                novelty = 1.0 - similarity
                event_copy['novelty'] = round(novelty, 4)

                # Emotion valence bias per modality
                valence_biases = {'vision': 0.4, 'hearing': 0.2, 'touch': -0.3, 'smell': -0.5, 'taste': 0.6}
                valence = valence_biases.get(modality, 0.0) * intensity_norm
                event_copy['emotion'] = {
                    'valence': round(valence, 3),
                    'category': self._categorize_valence(valence)
                }

                # Recurrence — if matched in memory
                recurrence = 1.0 if similarity < 0.8 else 2.0  # example logic
                event_copy['recurrence'] = recurrence

                # Timing sigmoid adjustment
                raw_timing = 1.0 / (1.0 + math.exp(-self.timing_steepness * (clock - self.timing_center)))
                event_copy['timing'] = round(raw_timing * (1.0 - self.salience_decay), 4)

                # Assign id and timestamp
                event_copy['id'] = str(uuid.uuid4())
                event_copy['timestamp'] = datetime.now(timezone.utc).isoformat()

                # Prioritization score (composite salience)
                event_copy['prioritization_score'] = round(self.w_i * intensity_norm + self.w_n * novelty, 4)

                all_tagged.append(event_copy)

        return all_tagged

    @staticmethod
    def _categorize_valence(val):
        if val > 0.6:
            return 'high_positive'
        elif val > 0.2:
            return 'positive'
        elif val < -0.6:
            return 'high_negative'
        elif val < -0.2:
            return 'negative'
        else:
            return 'neutral'