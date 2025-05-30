import random
from .salience import SalienceTagger
from . import memory

class SensoryInputSystem:
    """
    Sensory input system integrating salience tagging and memory storage.
    Supports awake/asleep cycles with explore, soothe, light_replay, and overnight consolidation.
    """
    MODALITIES = ['vision', 'hearing', 'touch', 'smell', 'taste']

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

        # Memory stores
        self.memory_buffer = memory.MemoryBuffer()
        self.long_term_storage = memory.LongTermStorage()

        # Salience tagger
        w_i, w_n = salience_weights
        self.salience_tagger = SalienceTagger(
            memory_store=self.memory_buffer,
            w_i=w_i,
            w_n=w_n,
            salience_decay=salience_decay
        )

        # Daytime mode probabilities
        self.mode_weights = {'explore': 0.5, 'soothe': 0.3, 'light_replay': 0.2}

    def update_clock(self):
        """Advance clock, update state timer, and handle state transitions."""
        self.clock += 1
        self.state_timer -= 1
        if self.state_timer <= 0:
            self._transition_state()

    def _transition_state(self):
        """Toggle awake/asleep state and trigger consolidation on sleep entry."""
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
        """Generate sensory packet with events grouped by modality."""
        if self.state == 'awake':
            events = self._awake_cycle()
        else:
            events = self._sleep_cycle()

        # Group events by modality for easier downstream processing
        grouped_events = {mod: [] for mod in self.MODALITIES}
        for event in events:
            mod = event.get('modality', 'unknown')
            grouped_events.setdefault(mod, []).append(event)

        return {
            'clock': self.clock,
            'state': self.state,
            'senses_packet': grouped_events
        }

    def _awake_cycle(self):
        """Select mode weighted by probability and process sensory events."""
        mode = random.choices(
            list(self.mode_weights.keys()),
            weights=list(self.mode_weights.values())
        )[0]

        if mode == 'explore':
            return self._explore()
        if mode == 'soothe':
            return self._soothe()
        return self._light_replay()

    def _sleep_cycle(self):
        """Replay events from long-term storage during sleep."""
        return self._replay_long_term()

    def _simulate_senses(self, count=None, intensity_range=None, modality='generic'):
        """Generate raw sensory events tagged with modality."""
        if self.state == 'asleep':
            return []

        cnt = count if count is not None else random.randint(*self.senses_count_range)
        ir = intensity_range if intensity_range is not None else self.intensity_range
        dr = self.duration_range

        return [
            {
                'modality': modality,
                'intensity': random.uniform(ir[0], ir[1]),
                'duration': random.randint(dr[0], dr[1])
            }
            for _ in range(cnt)
        ]

    def _explore(self):
        """Simulate exploration: generate and tag events for all modalities."""
        all_events = []
        for modality in self.MODALITIES:
            events = self._simulate_senses(modality=modality)
            all_events.extend(events)

        tagged = self.salience_tagger.tag_events(all_events)
        self.memory_buffer.store_events(tagged)
        return tagged

    def _soothe(self):
        """Simulate soothing: low-intensity events for all modalities."""
        low_intensity_range = (
            self.intensity_range[0],
            (self.intensity_range[0] + self.intensity_range[1]) / 2
        )
        all_events = []
        for modality in self.MODALITIES:
            events = self._simulate_senses(intensity_range=low_intensity_range, modality=modality)
            all_events.extend(events)

        tagged = self.salience_tagger.tag_events(all_events)
        self.memory_buffer.store_events(tagged)
        return tagged

    def _light_replay(self):
        """Replay top salient short-term memory events."""
        return self.memory_buffer.replay_salient()

    def _consolidate(self):
        """Consolidate short-term events into long-term storage and cleanup."""
        self.memory_buffer.consolidate_to(self.long_term_storage)
        self.memory_buffer.cleanup_low_salience()

    def _replay_long_term(self):
        """Replay salient long-term memory events."""
        return self.long_term_storage.replay()