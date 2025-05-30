import math
import random
from collections import deque

class MemoryStore:
    """
    Base memory store for managing decay of salience over time.
    Internal use for both short-term and long-term storage.
    """
    def __init__(self):
        # base class, no init params for now
        pass

class MemoryBuffer(MemoryStore):
    """
    Short-term memory buffer with per-event salience, decay, and consolidation support.
    """
    def __init__(self, max_short_term=1000, low_salience_threshold=0.5):
        super().__init__()
        self.short_term = deque(maxlen=max_short_term)
        self.low_salience_threshold = low_salience_threshold

    def tick_decay(self):
        """
        Increment tag_age and apply exponential decay to each event's salience.
        """
        for event in list(self.short_term):
            event['tag_age'] = event.get('tag_age', 0) + 1
            rate = event.get('decay_rate', math.log(2)/2000)
            event['salience'] *= math.exp(-rate)

    def store_events(self, tagged_events):
        """
        Store new tagged events and assign half-life & decay rate.
        """
        for event in tagged_events:
            s0 = event.get('initial_salience', event.get('salience', 0))
            if s0 < self.low_salience_threshold:
                half_life = random.uniform(1200, 2400)
            else:
                half_life = random.uniform(2400, 4800)
            event['half_life'] = round(half_life, 4)
            event['decay_rate'] = math.log(2) / half_life
            event['tag_age'] = event.get('tag_age', 0)
            self.short_term.append(event)

    def consolidate_to(self, long_term_storage, threshold=0.5, boost_rate=0.1):
        """
        Boost and move high-salience events to long-term storage.
        """
        for event in list(self.short_term):
            init = event.get('initial_salience', event['salience'])
            event['salience'] += boost_rate * init
            if event['salience'] >= threshold:
                long_term_storage.store(event)
                try:
                    self.short_term.remove(event)
                except ValueError:
                    pass

    def cleanup_low_salience(self, min_salience=0.1):
        """
        Remove events below min salience threshold.
        """
        self.short_term = deque(
            [e for e in self.short_term if e.get('salience', 0) >= min_salience],
            maxlen=self.short_term.maxlen
        )

    def max_similarity(self, event):
        """
        Calculate max similarity to any event in short-term memory.
        """
        if not self.short_term:
            return 0.0
        sims = [self._event_similarity(event, p) for p in self.short_term]
        return max(sims)

    @staticmethod
    def _event_similarity(e1, e2):
        weights = {'duration': 0.1, 'intensity': 0.1, 'novelty': 0.3, 'timing': 0.2, 'prioritization_score': 0.3}
        sim = 0.0
        sim += weights['duration'] * (1 - abs(e1.get('duration', 0) - e2.get('duration', 0)) / 10)
        sim += weights['intensity'] * (1 - abs(e1.get('intensity', 0) - e2.get('intensity', 0)))
        return max(0.0, min(1.0, sim))

    def replay_salient(self, top_k=10):
        """
        Return the top_k most salient events.
        """
        return sorted(self.short_term, key=lambda e: e.get('salience', 0), reverse=True)[:top_k]


class LongTermStorage(MemoryStore):
    """
    Long-term storage for consolidated events.
    """
    def __init__(self):
        super().__init__()
        self.long_term = {}

    def store(self, event):
        """
        Store an event indexed by its ID.
        """
        self.long_term[event['id']] = event

    def replay(self, top_k=10):
        """
        Return top_k events sorted by salience.
        """
        events = list(self.long_term.values())
        return sorted(events, key=lambda e: e.get('salience', 0), reverse=True)[:top_k]