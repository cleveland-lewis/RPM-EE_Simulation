# sensory.py
# This module simulates a sensory input system that mimics biological sensory processing.
# It generates sensory events across multiple modalities, manages states like awake, fatigued,
# and asleep, and interacts with memory systems to tag, store, and consolidate sensory information.
# The system uses salience tagging to prioritize important events and modulates sensory input
# based on internal states, facilitating exploration, soothing, and replay behaviors.

import logging
import math
import random
from typing import Any, Mapping, TypedDict, cast

import numpy as np
from scipy.stats import poisson, expon, norm
try:
    # Package-relative imports when running via `import src.sensory`
    from .salience import SalienceTagger
    from . import memory
except ImportError:
    # Fallback for running sensory.py directly
    from salience import SalienceTagger
    import memory

logger = logging.getLogger(__name__)


class SensoryTick(TypedDict):
    """Schema for the payload emitted by `SensoryInputSystem.tick`."""

    attunement_score: float
    schema_stress: float
    avg_affect_feedback: float
    short_term_size: int
    long_term_size: int


def validate_tick_payload(payload: Mapping[str, Any]) -> SensoryTick:
    """Validate and normalize the payload emitted by `SensoryInputSystem.tick`.

    Ensures keys exist, numeric values are finite, and sizes are non-negative integers.
    Returns a typed dict to lock the interface for downstream consumers.
    """
    required = {
        "attunement_score": float,
        "schema_stress": float,
        "avg_affect_feedback": float,
        "short_term_size": int,
        "long_term_size": int,
    }
    missing = [k for k in required if k not in payload]
    if missing:
        raise ValueError(f"Sensory tick payload missing keys: {missing}")

    validated: dict[str, Any] = {}
    for key, expected_type in required.items():
        value = payload[key]
        if expected_type is float:
            if not isinstance(value, (int, float, np.floating)):
                raise ValueError(f"{key} must be numeric, got {type(value)}")
            numeric = float(value)
            if not math.isfinite(numeric):
                raise ValueError(f"{key} must be finite, got {value}")
            validated[key] = numeric
        else:
            if not isinstance(value, (int, np.integer)):
                raise ValueError(f"{key} must be an integer, got {type(value)}")
            integer = int(value)
            if integer < 0:
                raise ValueError(f"{key} must be non-negative, got {integer}")
            validated[key] = integer

    return cast(SensoryTick, validated)

class SensoryInputSystem:
    """
    SensoryInputSystem simulates sensory input
    across multiple modalities (vision, hearing, touch, smell, taste).
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
        low_salience_var_rate: float = 0.1,
        event_rate: int = 3,
        memory_buffer_size: int = 1000,
        memory_decay: float = 0.01,
        memory_prune_threshold: float = 0.2,
        py_random: random.Random | None = None,
        np_random: np.random.Generator | None = None,
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

        self.py_rng = py_random or random.Random()
        self.np_rng = np_random or np.random.default_rng()

        # Inter-individual (agent) noise factors
        self.attunement_bias = self.np_rng.uniform(-0.07, 0.07)
        self.stress_bias = self.np_rng.uniform(-0.09, 0.09)

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
        self.poisson_rate_mu = self.event_rate
        self.poisson_rate_sigma = max(0.2, 0.25 * self.event_rate)

        # Randomize salience thresholds if not provided, to simulate individual variability
        if low_salience_threshold is None:
            low_salience_threshold = self.py_rng.uniform(0.3, 0.7)
        if high_salience_threshold is None:
            high_salience_threshold = self.py_rng.uniform(0.7, 0.95)

        # New variability and memory parameters
        self.low_salience_var_rate = low_salience_var_rate
        self.memory_buffer_size    = memory_buffer_size
        self.memory_decay          = memory_decay
        self.memory_prune_th       = memory_prune_threshold

        # Initialize memory buffer with hooks
        self.memory_buffer = memory.MemoryBuffer(
            max_short_term=memory_buffer_size,
            low_salience_threshold=low_salience_threshold,
            high_salience_threshold=high_salience_threshold,
            pre_store_hook=self._pre_store_hook,
            post_store_hook=self._post_store_hook,
        )
        # Lightweight per‑modality metrics updated after each store
        self._stored_by_modality = {m: 0 for m in self.MODALITIES}
        self._novelty_ema = {m: 0.0 for m in self.MODALITIES}
        self._ema_alpha = 0.05

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

        # ---- Bernoulli retrieval model (Beta–Bernoulli) counters ----
        # Slightly wider prior (α=β=5) keeps early posterior near 0.5
        # so attunement moves gradually instead of spiking.
        self.alpha0 = 5.0            # prior α
        self.beta0  = 5.0            # prior β
        self.retrieval_attempts   = 0
        self.retrieval_successes  = 0
    def _pre_store_hook(self, event: dict) -> dict:
        """Normalize/augment an event before storing into WM.
        - Ensure an `id`
        - Set `initial_salience` if missing
        - Provide `prioritization_score` and `timing`
        - Slightly down-weight salience/novelty if highly similar to WM contents
        """
        e = dict(event)  # shallow copy to avoid mutating caller
        # Ensure stable-ish id
        if 'id' not in e or e.get('id') is None:
            mod = e.get('modality', 'mm')
            e['id'] = f"{mod}-{self.clock}-{self.py_rng.randrange(1_000_000)}"
        # Ensure timing present (use raw clock; normalization can be added later)
        if 'timing' not in e:
            try:
                e['timing'] = float(self.clock)
            except (ValueError, TypeError):
                e['timing'] = 0.0
        # Initial salience defaults to current salience
        if 'salience' in e and 'initial_salience' not in e:
            try:
                e['initial_salience'] = float(e['salience'])
            except (ValueError, TypeError):
                pass
        # Prioritization mirrors salience if missing
        if 'prioritization_score' not in e and 'salience' in e:
            try:
                e['prioritization_score'] = float(e['salience'])
            except (ValueError, TypeError):
                pass
        # Ensure novelty key exists
        if 'novelty' not in e:
            e['novelty'] = 0.0
        # If this looks very similar to existing WM content, softly down-weight
        try:
            _, _, scores = self.memory_buffer.match_patterns([e], return_scores=True)
            sim = scores[0]
            thr = getattr(self.memory_buffer, 'similarity_threshold', 0.8)
            if sim > thr:
                # Reduce novelty and slightly reduce salience to avoid WM clutter
                try:
                    e['novelty'] = max(0.0, float(e.get('novelty', 0.0)) * 0.5)
                except (ValueError, TypeError):
                    pass
                if 'salience' in e:
                    try:
                        e['salience'] = max(0.0, float(e['salience']) * 0.85)
                    except (ValueError, TypeError):
                        pass
        except Exception as sim_err:
            # If similarity check fails, proceed without adjustment but make it visible
            logger.warning("pre_store similarity adjustment failed: %s", sim_err, exc_info=sim_err)
        return e

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
        mode = self.py_rng.choices(list(self.mode_weights.keys()), weights=list(self.mode_weights.values()))[0]
        events = []
        if mode == 'explore':
            events.extend(self._explore())
        elif mode == 'soothe':
            events.extend(self._soothe())
        else:
            events.extend(self._light_replay())

        # Add highly variable events rarely to simulate unexpected stimuli
        if self.py_rng.random() < self.highly_variable_rate:
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
        count = self.py_rng.randint(1, 3)
        events = []
        for _ in range(count):
            low_edge = self.intensity_range[0]
            high_edge = self.intensity_range[1]
            # Randomly choose low or high intensity near edges of range
            if self.py_rng.random() < 0.5:
                intensity_val = self.py_rng.uniform(low_edge, low_edge + 0.1)
            else:
                intensity_val = self.py_rng.uniform(high_edge - 0.1, high_edge)
            duration_val = self.py_rng.randint(self.duration_range[0], self.duration_range[1])
            modality = self.py_rng.choice(self.MODALITIES)
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

        cnt = count if count is not None else self.py_rng.randint(*self.senses_count_range)
        ir = intensity_range if intensity_range else self.intensity_range
        dr = self.duration_range

        events = []
        for _ in range(cnt):
            # Optionally customize intensity ranges per modality here
            # if modality == 'vision':
            #     ir = (0.2, 0.8)
            intensity_val = self.py_rng.uniform(ir[0], ir[1])
            duration_val = self.py_rng.randint(dr[0], dr[1])
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

    # ------------------------------------------------------------------
    # Lightweight tick used by run_simulation for per‑tick metrics
    # ------------------------------------------------------------------
    def tick(self, memory_prune_threshold: float = None) -> dict:
        """
        Advance the clock, generate a few events, decay/prune memory,
        and return attunement_score, schema_stress, and avg_affect_feedback.
        Attunement is modelled as the posterior mean probability that a retrieved
        long‑term cue correctly predicts the next incoming social cue, estimated
        via a Beta‑Bernoulli process with p = LT / (LT + ST).
        """
        # Simulate state-dependent, noisy event rate (inhomogeneous Poisson process)
        base_rate = self.poisson_rate_mu
        if self.state == 'fatigued':
            base_rate *= 0.5
        elif self.state == 'asleep':
            base_rate *= 0.1

        poisson_rate = max(0.1, self.np_rng.normal(base_rate, self.poisson_rate_sigma))
        n_events = self.np_rng.poisson(poisson_rate)
        n_events = max(1, int(n_events))

        new_events = self._simulate_senses(
            count=n_events,
            modality=self.py_rng.choice(self.MODALITIES)
        )
        tagged = self.salience_tagger.tag_events(new_events)
        self.memory_buffer.store_events(tagged)

        # Decay memory each tick
        self.memory_buffer.tick_decay(memory_prune_threshold=memory_prune_threshold)

        # Update clock & possibly state
        self.update_clock()

        # --- Metrics (Bernoulli retrieval model) ---
        st_sz = len(self.memory_buffer.short_term)
        lt_sz = len(self.long_term_storage.long_term)
        denom = max(self.memory_buffer_size, 1)

        # Simulate one "social‑prediction" retrieval attempt.
        #   Success probability ≈ proportion of familiar (LT) cues among all active cues.
        #   When many fresh (ST) cues dominate, mismatch risk is higher ⇒ lower p.
        success_prob = lt_sz / max(lt_sz + st_sz, 1)
        self.retrieval_attempts += 1
        if self.py_rng.random() < success_prob:
            self.retrieval_successes += 1

        # Posterior mean of Beta(α, β) after observing successes / failures
        posterior_alpha = self.alpha0 + self.retrieval_successes
        posterior_beta  = self.beta0  + (self.retrieval_attempts - self.retrieval_successes)
        attunement_score = posterior_alpha / (posterior_alpha + posterior_beta)

        # Keep existing definition for schema_stress
        schema_stress = float(np.clip(st_sz / denom, 0.0, 1.0))
        # Apply inter-individual biases
        attunement_score = float(np.clip(attunement_score + self.attunement_bias, 0.0, 1.0))
        schema_stress = float(np.clip(schema_stress + self.stress_bias, 0.0, 1.0))

        # Affect feedback: mix attunement (+) and stress (−) plus small noise
        epsilon = self.np_rng.normal(0.0, 0.05)  # Gaussian noise
        avg_affect_feedback = 1.4 * attunement_score - 0.8 * schema_stress + epsilon # Now a stronger weight
        avg_affect_feedback = float(np.clip(avg_affect_feedback, -1.0, 1.0))  # keep in [-1,1]

        payload = {
            "attunement_score":    attunement_score,
            "schema_stress":       schema_stress,
            "avg_affect_feedback": avg_affect_feedback,
            "short_term_size":     st_sz,
            "long_term_size":      lt_sz,
        }
        return validate_tick_payload(payload)
    def _post_store_hook(self, event: dict) -> None:
        """After storing to WM, update simple, side‑effect‑free metrics.
        Maintains per‑modality counts and a small EWMA of novelty.
        No control‑flow changes here (keeps behavior stable).
        """
        try:
            mod = event.get('modality', 'unknown')
            if mod in self._stored_by_modality:
                self._stored_by_modality[mod] += 1
            nov = float(event.get('novelty', 0.0))
            if mod in self._novelty_ema:
                a = self._ema_alpha
                self._novelty_ema[mod] = (1 - a) * self._novelty_ema[mod] + a * nov
        except Exception as hook_err:
            # Metrics are best‑effort only, but surface failures for debugging
            event_id = event.get('id', '<unknown>') if isinstance(event, Mapping) else '<unknown>'
            logger.warning("post_store_hook metrics update failed for event %s: %s", event_id, hook_err, exc_info=hook_err)
        # No return value required; hook is for side‑effects only
        return None
