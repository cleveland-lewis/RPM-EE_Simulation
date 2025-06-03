import datetime as real_datetime
from datetime import datetime, timezone
import uuid

class SalienceTagger:
    MODALITIES = ['vision', 'hearing', 'touch', 'smell', 'taste']

    def __init__(self, memory_store, w_i=0.5, w_n=0.5, salience_decay=0.01):
        self.memory_store = memory_store
        self.w_i = w_i
        self.w_n = w_n
        self.salience_decay = salience_decay
        self.timing_center = 250
        self.timing_steepness = 0.1

    def tag_input(self, packet):
        events = []
        for modality in self.MODALITIES:
            if modality not in packet:
                continue
            for event in packet[modality]:
                event_copy = event.copy()
                event_copy['modality'] = modality
                event_copy['state'] = packet['state']
                event_copy['id'] = str(uuid.uuid4())
                event_copy['timestamp'] = real_datetime.datetime.utcnow().replace(tzinfo=real_datetime.timezone.utc).isoformat()
                event_copy['novelty'] = max(0.2, self.memory_store.max_similarity(event))
                event_copy['recurrence'] = 1.0
                raw_timing = 1.0 / (1.0 + pow(2.71828, -self.timing_steepness * (packet['clock'] - self.timing_center)))
                event_copy['timing'] = round(raw_timing * (1.0 - self.salience_decay), 4)
                event_copy['emotion'] = self.compute_emotion(event_copy)
                event_copy['prioritization_score'] = self.w_i * event_copy['intensity'] + self.w_n * event_copy['novelty']
                events.append(event_copy)
        return events

    def compute_emotion(self, event):
        biases = {'vision':0.4, 'hearing':0.2, 'touch':-0.3, 'smell':-0.5, 'taste':0.6}
        valence = round(biases.get(event['modality'], 0.0), 3)
        if valence > 0.6:
            category = 'high_positive'
        elif valence > 0.2:
            category = 'positive'
        elif valence < -0.6:
            category = 'high_negative'
        elif valence < -0.2:
            category = 'negative'
        else:
            category = 'neutral'
        return {'valence': valence, 'category': category}