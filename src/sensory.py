# sensory.py
# This module simulates a sensory input system that mimics biological sensory processing.
# It generates sensory events across multiple modalities, manages states like awake, fatigued,
# and asleep, and interacts with memory systems to tag, store, and consolidate sensory information.
# The system uses salience tagging to prioritize important events and modulates sensory input
# based on internal states, facilitating exploration, soothing, and replay behaviors.

import random
from src.salience import SalienceTagger
from . import memory

class SensoryInputSystem:
    """
    SensoryInputSystem simulates sensory input across multiple modalities (vision, hearing, touch, smell, taste).
    It manages internal states (awake, fatigued, asleep) that influence sensory input patterns,
    and interacts with memory systems for tagging, storing, and consolidating sensory events.
    """

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
        highly_variable_rate=0.1,
        event_rate: int = 3
    ):
        """
        Initialize the sensory input system with parameters controlling sensory generation,
        state durations, salience tagging, and memory thresholds.

        Parameters:
        - neurotype: str, type of neural processing (default 'neurotypical')
        - context: str, contextual label for sensory processing (default 'default')
        - senses_count_range: tuple(int, int), min and max number of sensory events generated
        - intensity_range: tuple(float, float), min and max intensity values for sensory events
        - duration_range: tuple(int, int), min and max duration values for sensory events
        - awake_ticks: int, number of ticks the system stays awake before state transition
        - fatigue_ticks: int, duration of fatigued state in ticks
        - asleep_ticks: int, duration of asleep state in ticks
        - salience_weights: tuple(float, float), weights for intensity and novelty in salience tagging
        - salience_decay: float, decay rate for salience over time
        - low_salience_threshold: float or None, threshold below which events are considered low salience
        - high_salience_threshold: float or None, threshold above which events are highly salient
        - highly_variable_rate: float, probability of generating rare, highly variable sensory events
        - event_rate: int, number of sensory events generated per tick
        """

        # Initialize internal clock and state management
        self.clock = 0
        self.state = 'awake'
        self.state_durations = {'awake': awake_ticks, 'fatigued': fatigue_ticks, 'asleep': asleep_ticks}
        self.state_timer = self.state_durations[self.state]

        # Store parameters related to sensory event generation and variability
        self.neurotype = neurotype
        self.context = context
        self.senses_count_range = senses_count_range
        self.intensity_range = intensity_range
        self.duration_range = duration_range
        self.highly_variable_rate = highly_variable_rate
        # Rate of sensory events per tick, configured via batch UI
        self.event_rate = event_rate

        # Randomize salience thresholds if not provided, to simulate individual variability
        if low_salience_threshold is None:
            low_salience_threshold = random.uniform(0.3, 0.7)
        if high_salience_threshold is None:
            high_salience_threshold = random.uniform(0.7, 0.95)

        # Initialize memory buffer with salience thresholds for filtering events
        self.memory_buffer = memory.MemoryBuffer(
            low_salience_threshold=low_salience_threshold,
            high_salience_threshold=high_salience_threshold
        )
        # Initialize long term storage for consolidated memories
        self.long_term_storage = memory.LongTermStorage()

        # Setup salience tagger with weights for intensity and novelty, and decay factor
        w_i, w_n = salience_weights
        self.salience_tagger = SalienceTagger(
            memory_store=self.memory_buffer,
            w_i=w_i,
            w_n=w_n,
            salience_decay=salience_decay
        )

        # Define mode weights to probabilistically select exploration, soothing, or replay modes during awake state
        self.mode_weights = {'explore': 0.5, 'soothe': 0.3, 'light_replay': 0.2}

    def update_clock(self):
        """
        Advance the internal clock by one tick, decrement the state timer,
        and trigger state transitions when timers expire.
        This method simulates the passage of time and state cycling.
        """
        self.clock += 1
        self.state_timer -= 1
        if self.state_timer <= 0:
            self._transition_state()

    def _transition_state(self):
        """
        Internal method to cycle through states in sequence:
        awake -> fatigued -> asleep -> awake.
        Handles resetting state timers and triggers sleep entry processing.
        """
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
        """
        Called when entering the asleep state.
        Triggers consolidation of memories from short-term buffer to long-term storage.
        """
        self._consolidate()

    def generate_input(self):
        """
        Generate sensory input events based on the current state.
        Awake state produces full range sensory inputs with different modes,
        fatigued state produces reduced or soothing inputs,
        asleep state produces minimal, low intensity inputs.

        Returns:
            A dictionary packet containing the clock, current state,
            and grouped sensory events by modality.
        """
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

        # Group events by modality in the returned packet for easy access
        grouped_events = {mod: [] for mod in self.MODALITIES}
        for event in events:
            mod = event.get('modality')
            if mod in self.MODALITIES:
                grouped_events[mod].append(event)
            else:
                # Handle unexpected modalities by grouping under 'unknown'
                grouped_events.setdefault('unknown', []).append(event)

        # Construct the sensory input packet with clock, state, and events
        packet = {
            'clock': self.clock,
            'state': self.state,
        }
        for modality, events_list in grouped_events.items():
            packet[modality] = events_list

        return packet

    def _awake_cycle(self):
        """
        Generate sensory events during the awake state.
        Randomly selects a mode based on predefined weights:
        'explore' for diverse sensory input,
        'soothe' for calming input,
        'light_replay' for replaying salient memories.
        Occasionally adds highly variable, rare sensory events to introduce novelty.
        """
        mode = random.choices(list(self.mode_weights.keys()), weights=list(self.mode_weights.values()))[0]
        events = []
        if mode == 'explore':
            events.extend(self._explore())
        elif mode == 'soothe':
            events.extend(self._soothe())
        else:
            events.extend(self._light_replay())

        # Add highly variable events rarely to simulate unexpected stimuli
        if random.random() < self.highly_variable_rate:
            events.extend(self._highly_variable_events())

        # Enforce configured event rate
        if len(events) > self.event_rate:
            events = events[:self.event_rate]

        return events

    def _highly_variable_events(self):
        """
        Generate a small number of sensory events with intensities near the edges of the intensity range.
        These events simulate rare, highly variable stimuli that can capture attention.
        Returns a list of such event dictionaries.
        """
        count = random.randint(1, 3)
        events = []
        for _ in range(count):
            low_edge = self.intensity_range[0]
            high_edge = self.intensity_range[1]
            # Randomly choose low or high intensity near edges of range
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
        """
        Generate fixed low intensity sensory events for all modalities to simulate sensory input during sleep.
        These events are minimal and have fixed duration and low intensity,
        representing the reduced sensory processing in sleep state.
        """
        all_events = []
        for modality in self.MODALITIES:
            all_events.append({
                'modality': modality,
                'intensity': 0.2,  # low constant intensity for sleep
                'duration': 3      # fixed duration for sleep sensory events
            })
        return all_events

    def transition_state(self):
        """
        Public method for external triggers (e.g., tests) to force a state transition.
        Mirrors the internal _transition_state method.
        """
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
        """
        Helper method to generate a list of sensory events for a given modality.
        Parameters:
        - count: number of events to generate (random within range if None)
        - intensity_range: tuple specifying intensity bounds (uses default if None)
        - modality: sensory modality string

        Returns a list of sensory event dictionaries with modality, intensity, and duration.
        Returns empty list if system is asleep (no sensory input).
        """
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
        """
        Generate diverse sensory events across all modalities simulating exploratory behavior.
        Tags events with salience scores and stores them in the memory buffer.
        Returns the tagged events.
        """
        all_events = []
        for modality in self.MODALITIES:
            events = self._simulate_senses(modality=modality)
            all_events.extend(events)
        tagged = self.salience_tagger.tag_events(all_events)
        self.memory_buffer.store_events(tagged)
        return tagged

    def _soothe(self):
        """
        Generate lower intensity sensory events across all modalities simulating soothing behavior.
        Uses a reduced intensity range to produce calming sensory input.
        Tags and stores events similarly to _explore.
        Returns the tagged events.
        """
        low_intensity_range = (self.intensity_range[0], (self.intensity_range[0] + self.intensity_range[1]) / 2)
        all_events = []
        for modality in self.MODALITIES:
            events = self._simulate_senses(intensity_range=low_intensity_range, modality=modality)
            all_events.extend(events)
        tagged = self.salience_tagger.tag_events(all_events)
        self.memory_buffer.store_events(tagged)
        return tagged

    def _light_replay(self):
        """
        Retrieve and return salient sensory events from the memory buffer to simulate light replay.
        This can help reinforce memory traces during awake periods.
        """
        return self.memory_buffer.replay_salient()

    def _consolidate(self):
        """
        Consolidate memories by transferring salient events from the short-term memory buffer
        to long-term storage, then clean up low salience events from the buffer.
        This simulates memory consolidation during sleep.
        """
        self.memory_buffer.consolidate_to(self.long_term_storage)
        self.memory_buffer.cleanup_low_salience()

    def _replay_long_term(self):
        """
        Replay memories from long-term storage.
        This method can be used to simulate memory recall or deep replay processes.
        """
        return self.long_term_storage.replay()
