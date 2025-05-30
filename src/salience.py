import uuid
from datetime import datetime

class SalienceTagger:
    """
    Computes and tags each sensory event with an initial salience score
    based on intensity and novelty relative to past memory.
    """
    def __init__(self, memory_store, w_I=0.6, w_N=0.4, salience_decay=0.01):
        # memory_store must provide max_similarity(event) → float in [0,1]
        self.memory_store = memory_store
        # weight on event intensity
        self.w_I = w_I
        # weight on event novelty
        self.w_N = w_N
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
            I = e.get('intensity', 0.0)
            I_norm = min(max(I, 0.0), 1.0)

            # Compute novelty: 1 - highest similarity to existing memories
            sim = self.memory_store.max_similarity(e)
            N = 1.0 - sim

            # Composite salience: weighted sum
            s = self.w_I * I_norm + self.w_N * N

            # Build tagged event
            e_tagged = e.copy()
            e_tagged.update({
                'id': str(uuid.uuid4()),
                'timestamp': datetime.utcnow().isoformat(),
                'novelty': round(N, 4),
                'initial_salience': round(s, 4),
                'salience': round(s, 4),
                'tag_age': 0,
                'decay_rate': self.salience_decay
            })
            tagged.append(e_tagged)

        return tagged
