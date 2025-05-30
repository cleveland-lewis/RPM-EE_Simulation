import random
#from .input_bias_filter import InputBiasFilter
from .salience import SalienceTagger
from . import memory


class SensoryInputSystem:
    """
    Sensory input system integrating salience tagging and memory storage.
    Supports awake/asleep cycles with explore, soothe, light_replay, and overnight consolidation.
    """
    def __init__(
        self,
        neurotype='neurotypical',
        context='default',
        senses_count_range=(0, 5),
        intensity_range=(0.1, 1.0),
        duration_range=(1, 10),
        awake_ticks=1700,
        asleep_ticks=700,
        salience_weights=(0.6, 0.4),
        salience_decay=0.01
    ):
        # Clock and state setup
        self.clock = 0
        self.state = 'awake'
        self.state_durations = {'awake': awake_ticks, 'asleep': asleep_ticks}
        self.state_timer = self.state_durations[self.state]

        # Sensory parameters
        self.neurotype = neurotype
        self.context = context
        self.senses_count_range = senses_count_range
        self.intensity_range = intensity_range
        self.duration_range = duration_range
        # Bias filter
        #self.input_bias_filter = InputBiasFilter(neurotype, context)

        # Memory stores
        self.memory_buffer = memory.MemoryBuffer()
        self.long_term_storage = memory.LongTermStorage()

        # Salience tagger
        w_I, w_N = salience_weights
        self.salience_tagger = SalienceTagger(
            memory_store=self.memory_buffer,
            w_I=w_I,
            w_N=w_N,
            salience_decay=salience_decay
        )

        # Daytime mode probabilities
        self.mode_weights = {'explore': 0.5, 'soothe': 0.3, 'light_replay': 0.2}

    def update_clock(self):
        """
        Advance the internal clock, decrement timer, and handle state transitions.
        """
        self.clock += 1
        self.state_timer -= 1
        if self.state_timer <= 0:
            self._transition_state()

    def _transition_state(self):
        """
        Switch between awake and asleep states, triggering consolidation on sleep entry.
        """
        if self.state == 'awake':
            self.state = 'asleep'
            self.state_timer = self.state_durations['asleep']
            self._on_sleep_entry()
        else:
            self.state = 'awake'
            self.state_timer = self.state_durations['awake']

    def _on_sleep_entry(self):
        """Perform consolidation immediately upon entering sleep."""
        self._consolidate()

    def generate_input(self):
        """
        Generate a sensory packet: choose awake vs sleep processing,
        and return packet with metadata.
        """
        if self.state == 'awake':
            events = self._awake_cycle()
        else:
            events = self._sleep_cycle()

        return {
            'clock': self.clock,
            'state': self.state,
            'senses_packet': events
        }

    def _awake_cycle(self):
        """
        During awake state, pick a mode by weighted probability and process.
        Modes:
          - explore: simulate new events and store
          - soothe: simulate low-intensity events and store
          - light_replay: replay salient short-term events
        """
        mode = random.choices(
            list(self.mode_weights.keys()),
            weights=self.mode_weights.values()
        )[0]

        if mode == 'explore':
            return self._explore()
        if mode == 'soothe':
            return self._soothe()
        return self._light_replay()

    def _sleep_cycle(self):
        """
        During sleep state, replay from long-term storage only.
        """
        return self._replay_long_term()

    def _simulate_senses(self, count=None, intensity_range=None):
        """
        Generate raw sensory events with 'intensity' and 'duration'.
        """
        if self.state == 'asleep':
            return []

        cnt = count if count is not None else random.randint(*self.senses_count_range)
        ir = intensity_range if intensity_range is not None else self.intensity_range
        dr = self.duration_range

        return [
            {
                'intensity': random.uniform(ir[0], ir[1]),
                'duration': random.randint(dr[0], dr[1])
            }
            for _ in range(cnt)
        ]

    def _explore(self):
        """
        Simulate exploration: tag new events and store in short-term buffer.
        """
        events = self._simulate_senses()
        tagged = self.salience_tagger.tag_events(events)
        # Store all tagged events at once
        self.memory_buffer.store_events(tagged)
        return tagged

    def _soothe(self):
        """
        Simulate soothing stimuli: low-intensity events, tag, and store.
        """
        low_int = (
            self.intensity_range[0],
            (self.intensity_range[0] + self.intensity_range[1]) / 2
        )
        events = self._simulate_senses(intensity_range=low_int)
        tagged = self.salience_tagger.tag_events(events)
        self.memory_buffer.store_events(tagged)
        return tagged

    def _light_replay(self):
        """
        Replay salient events from short-term memory during rest.
        """
        return self.memory_buffer.replay_salient()

    def _consolidate(self):
        """
        Consolidate short-term into long-term storage and clean up.
        """
        self.memory_buffer.consolidate_to(self.long_term_storage)
        self.memory_buffer.cleanup_low_salience()

    def _replay_long_term(self):
        """
        Replay events from long-term storage during sleep.
        """
        return self.long_term_storage.replay()

