import uuid
from datetime import datetime, timezone

class SalienceTagger:
    """
    Computes and tags each sensory event with an initial salience score
    based on intensity and novelty relative to memory.
    """
    MODALITIES = ['vision', 'hearing',]
    def __init__(self, memory_store, w_i=0.6, w_n=0.4, salience_decay=0.01):
        # memory_store must provide max_similarity(event) → float in [0,1]
        self.memory_store = memory_store
        # weight on event intensity
        self.w_i = w_i
        # weight on event novelty
        self.w_n = w_n
        # per-tick decay rate for salience
        self.salience_decay = salience_decay

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