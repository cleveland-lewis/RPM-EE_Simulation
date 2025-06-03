import random
from src.salience import SalienceTagger
from . import memory

class SensoryInputSystem:
    MODALITIES = ['vision', 'hearing', 'touch', 'smell', 'taste']

    def __init__(
        self,
        neurotype='neurotypical',
        context='default',
        senses_count_range=(1, 10),
        intensity_range=(0.1, 1.0),
        duration_range=(1, 10),
        awake_ticks=1300,
        fatigue_ticks=400,
        asleep_ticks=700,
        salience_weights=(0.6, 0.4),
        salience_decay=0.01,
        low_salience_threshold=None,
        high_salience_threshold=None,
        highly_variable_rate=0.1
    ):
        self.clock = 0
        self.state = 'awake'
        self.state_durations = {'awake': awake_ticks, 'fatigued': fatigue_ticks, 'asleep': asleep_ticks}
        self.state_timer = self.state_durations[self.state]

        self.neurotype = neurotype
        self.context = context
        self.senses_count_range = senses_count_range
        self.intensity_range = intensity_range
        self.duration_range = duration_range
        self.highly_variable_rate = highly_variable_rate

        # --- Randomize thresholds if not provided ---
        if low_salience_threshold is None:
            low_salience_threshold = random.uniform(0.3, 0.7)
        if high_salience_threshold is None:
            high_salience_threshold = random.uniform(0.7, 0.95)

        self.memory_buffer = memory.MemoryBuffer(
            low_salience_threshold=low_salience_threshold,
            high_salience_threshold=high_salience_threshold
        )
        self.long_term_storage = memory.LongTermStorage()

        w_i, w_n = salience_weights
        self.salience_tagger = SalienceTagger(
            memory_store=self.memory_buffer,
            w_i=w_i,
            w_n=w_n,
            salience_decay=salience_decay
        )

        self.mode_weights = {'explore': 0.5, 'soothe': 0.3, 'light_replay': 0.2}

    def update_clock(self):
        self.clock += 1
        self.state_timer -= 1
        if self.state_timer <= 0:
            self._transition_state()

    def _transition_state(self):
        # Cycle through states: awake -> fatigued -> asleep -> awake
        if self.state == 'awake':
            self.state = 'fatigued'
            self.state_timer = self.state_durations['fatigued']
        elif self.state == 'fatigued':
            self.state = 'asleep'
            self.state_timer = self.state_durations['asleep']
            self._on_sleep_entry()
        else:  # asleep
            self.state = 'awake'
            self.state_timer = self.state_durations['awake']

    def _on_sleep_entry(self):
        # Perform consolidation on sleep entry
        self._consolidate()

    def generate_input(self):
        # Produce sensory input according to current state
        if self.state == 'awake':
            # Full range sensory input with exploration mode
            events = self._awake_cycle()
        elif self.state == 'fatigued':
            # Reduced sensory input or soothe mode
            events = self._soothe()
        elif self.state == 'asleep':
            # Minimal sensory input, fixed low intensity events
            events = self._sleep_cycle()
        else:
            events = []

        # Group events by modality in the returned packet
        grouped_events = {mod: [] for mod in self.MODALITIES}
        for event in events:
            mod = event.get('modality')
            if mod in self.MODALITIES:
                grouped_events[mod].append(event)
            else:
                grouped_events.setdefault('unknown', []).append(event)

        packet = {
            'clock': self.clock,
            'state': self.state,
        }
        for modality, events_list in grouped_events.items():
            packet[modality] = events_list

        return packet

    def _awake_cycle(self):
        # Exploration mode: random sensory events per modality
        mode = random.choices(list(self.mode_weights.keys()), weights=list(self.mode_weights.values()))[0]
        events = []
        if mode == 'explore':
            events.extend(self._explore())
        elif mode == 'soothe':
            events.extend(self._soothe())
        else:
            events.extend(self._light_replay())

        # Add highly variable events rarely
        if random.random() < self.highly_variable_rate:
            events.extend(self._highly_variable_events())

        return events

    def _highly_variable_events(self):
        # Generate a small number of events (e.g., 1 to 3)
        count = random.randint(1, 3)
        events = []
        for _ in range(count):
            # Randomly pick low or high intensity near edges of range
            low_edge = self.intensity_range[0]
            high_edge = self.intensity_range[1]
            if random.random() < 0.5:
                intensity_val = random.uniform(low_edge, low_edge + 0.1)
            else:
                intensity_val = random.uniform(high_edge - 0.1, high_edge)
            duration_val = random.randint(self.duration_range[0], self.duration_range[1])
            modality = random.choice(self.MODALITIES)
            events.append({
                'modality': modality,
                'intensity': intensity_val,
                'duration': duration_val
            })
        return events

    def _sleep_cycle(self):
        # Fixed low intensity sensory events per modality to simulate sleep
        all_events = []
        for modality in self.MODALITIES:
            all_events.append({
                'modality': modality,
                'intensity': 0.2,  # low constant intensity for sleep
                'duration': 3      # fixed duration for sleep sensory events
            })
        return all_events

    def transition_state(self):
        # Rename from _transition_state to public method for tests
        if self.state == 'awake':
            self.state = 'fatigued'
            self.state_timer = self.state_durations['fatigued']
        elif self.state == 'fatigued':
            self.state = 'asleep'
            self.state_timer = self.state_durations['asleep']
            self._on_sleep_entry()
        else:
            self.state = 'awake'
            self.state_timer = self.state_durations['awake']

    def _simulate_senses(self, count=None, intensity_range=None, modality='generic'):
        if self.state == 'asleep':
            return []

        cnt = count if count is not None else random.randint(*self.senses_count_range)
        ir = intensity_range if intensity_range else self.intensity_range
        dr = self.duration_range

        events = []
        for _ in range(cnt):
            # Optionally customize intensity ranges per modality here
            # if modality == 'vision':
            #     ir = (0.2, 0.8)
            intensity_val = random.uniform(ir[0], ir[1])
            duration_val = random.randint(dr[0], dr[1])
            events.append({
                'modality': modality,
                'intensity': intensity_val,
                'duration': duration_val
            })

        return events

    def _explore(self):
        all_events = []
        for modality in self.MODALITIES:
            events = self._simulate_senses(modality=modality)
            all_events.extend(events)
        tagged = self.salience_tagger.tag_events(all_events)
        self.memory_buffer.store_events(tagged)
        return tagged

    def _soothe(self):
        low_intensity_range = (self.intensity_range[0], (self.intensity_range[0] + self.intensity_range[1]) / 2)
        all_events = []
        for modality in self.MODALITIES:
            events = self._simulate_senses(intensity_range=low_intensity_range, modality=modality)
            all_events.extend(events)
        tagged = self.salience_tagger.tag_events(all_events)
        self.memory_buffer.store_events(tagged)
        return tagged

    def _light_replay(self):
        return self.memory_buffer.replay_salient()

    def _consolidate(self):
        self.memory_buffer.consolidate_to(self.long_term_storage)
        self.memory_buffer.cleanup_low_salience()

    def _replay_long_term(self):
        return self.long_term_storage.replay()
