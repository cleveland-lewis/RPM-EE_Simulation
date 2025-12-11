from typing import List, Dict, Tuple, Optional, Callable, Any
import copy
import math
import random
from collections import deque
import uuid
import logging

try:
    from .constants import (
        HALF_LIFE_LOW_SALIENCE_MIN, HALF_LIFE_LOW_SALIENCE_MAX,
        HALF_LIFE_MID_SALIENCE_MIN, HALF_LIFE_MID_SALIENCE_MAX,
        HALF_LIFE_HIGH_SALIENCE_MIN, HALF_LIFE_HIGH_SALIENCE_MAX,
        DEFAULT_LOW_SALIENCE_THRESHOLD, DEFAULT_HIGH_SALIENCE_THRESHOLD,
        DEFAULT_SIMILARITY_THRESHOLD, DEFAULT_MIN_SALIENCE_FOR_CLEANUP,
        DEFAULT_CONSOLIDATION_THRESHOLD, DEFAULT_CONSOLIDATION_BOOST_RATE,
        DEFAULT_CAPACITY_WEIGHT_SALIENCE, DEFAULT_CAPACITY_WEIGHT_RECENCY,
        DECAY_JITTER_MIN, DECAY_JITTER_MAX,
        MODULATION_CLIP_MIN, MODULATION_CLIP_MAX,
        MAX_BLEACH_COEFFICIENT, DEFAULT_EVENT_DURATION, DEFAULT_EVENT_INTENSITY
    )
except ImportError:
    from constants import (
        HALF_LIFE_LOW_SALIENCE_MIN, HALF_LIFE_LOW_SALIENCE_MAX,
        HALF_LIFE_MID_SALIENCE_MIN, HALF_LIFE_MID_SALIENCE_MAX,
        HALF_LIFE_HIGH_SALIENCE_MIN, HALF_LIFE_HIGH_SALIENCE_MAX,
        DEFAULT_LOW_SALIENCE_THRESHOLD, DEFAULT_HIGH_SALIENCE_THRESHOLD,
        DEFAULT_SIMILARITY_THRESHOLD, DEFAULT_MIN_SALIENCE_FOR_CLEANUP,
        DEFAULT_CONSOLIDATION_THRESHOLD, DEFAULT_CONSOLIDATION_BOOST_RATE,
        DEFAULT_CAPACITY_WEIGHT_SALIENCE, DEFAULT_CAPACITY_WEIGHT_RECENCY,
        DECAY_JITTER_MIN, DECAY_JITTER_MAX,
        MODULATION_CLIP_MIN, MODULATION_CLIP_MAX,
        MAX_BLEACH_COEFFICIENT, DEFAULT_EVENT_DURATION, DEFAULT_EVENT_INTENSITY
    )

logger = logging.getLogger(__name__)

class MemoryStore:
    """
    Base memory store for managing decay of salience over time.
    Internal use for both short-term and long-term storage.
    """
    def __init__(self):
        pass

class MemoryBuffer(MemoryStore):
    """
    Short-term memory buffer with per-event salience, decay, and consolidation support.
    """
    def __init__(
        self,
        max_short_term: int = 1000,
        low_salience_threshold: float = DEFAULT_LOW_SALIENCE_THRESHOLD,
        high_salience_threshold: float = 0.9,
        *,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
        similarity_weights: Optional[Dict[str, float]] = None,
        require_same_modality: bool = True,
        pre_store_hook: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
        post_store_hook: Optional[Callable[[Dict[str, Any]], None]] = None,
        recency_tau: float = 500.0,
    ):
        super().__init__()
        self.short_term = deque(maxlen=max_short_term)
        self.low_salience_threshold = low_salience_threshold
        self.high_salience_threshold = high_salience_threshold
        self.similarity_threshold = similarity_threshold
        self.similarity_weights = (
            similarity_weights.copy() if similarity_weights is not None else {
                'duration': DEFAULT_EVENT_DURATION,
                'intensity': DEFAULT_EVENT_INTENSITY,
                'novelty': 0.3,
                'timing': 0.2,
                'prioritization_score': 0.3,
            }
        )
        # --- Literature-grounded, neutral-by-default encoding coefficients ---
        # These allow affect (valence/arousal), stimulus features, and exposure context
        # to scale encoding strength without changing current behavior (defaults are neutral).
        self.encoding_coeffs = {
            'c_valence'   : 0.0,  # |valence| weight
            'c_arousal'   : 0.0,  # arousal (0..1)
            'c_meaning'   : 0.0,  # meaningfulness (0..1)
            'c_color'     : 0.0,  # color richness (0..1)
            'spacing_gain': 0.0,  # sublinear repetition gain on half-life
        }
        self.exposure_multipliers = {
            'real': 1.0,
            'vr'  : 1.0,
            '2d'  : 1.0,
        }
        self.require_same_modality = require_same_modality
        self.pre_store_hook = pre_store_hook
        self.post_store_hook = post_store_hook
        self._next_id = 1  # auto-ID counter for events lacking an explicit id
        self._tick = 0     # internal tick counter advanced by tick_decay
        self.recency_tau = float(recency_tau)
        # Ensure a 'recency' weight exists (default 0.0 for backward-compat)
        if 'recency' not in self.similarity_weights:
            self.similarity_weights['recency'] = 0.0

        # Optional semanticization policy (neutral by default)
        self._semanticization = {
            'auto': False,      # if True, apply default transform during consolidation when conditions are met
            'gain': 0.0,        # strength of context-bleaching (0 = off)
            'min_age': 0,       # minimum tag_age to start semanticization
            'min_repeats': 0,   # minimum repeat_count (or recurrence) to start semanticization
            'max_bleach': MAX_BLEACH_COEFFICIENT,  # cap on how much to attenuate episodic context fields
        }
    def set_encoding_policy(
        self,
        *,
        coeffs: Optional[Dict[str, float]] = None,
        exposure_multipliers: Optional[Dict[str, float]] = None
    ) -> None:
        """Update optional encoding knobs. Defaults keep behavior unchanged."""
        if coeffs:
            self.encoding_coeffs.update({k: float(v) for k, v in coeffs.items() if k in self.encoding_coeffs})
        if exposure_multipliers:
            for k, v in exposure_multipliers.items():
                self.exposure_multipliers[k] = float(v)

    def set_semanticization_policy(
        self,
        *,
        auto: Optional[bool] = None,
        gain: Optional[float] = None,
        min_age: Optional[int] = None,
        min_repeats: Optional[int] = None,
        max_bleach: Optional[float] = None,
    ) -> None:
        """Configure optional semanticization during consolidation.
        Defaults keep behavior unchanged (auto=False, gain=0).
        """
        if auto is not None:
            self._semanticization['auto'] = bool(auto)
        if gain is not None:
            self._semanticization['gain'] = float(gain)
        if min_age is not None:
            self._semanticization['min_age'] = int(min_age)
        if min_repeats is not None:
            self._semanticization['min_repeats'] = int(min_repeats)
        if max_bleach is not None:
            self._semanticization['max_bleach'] = float(max_bleach)

    def _semanticize_event(self, e: Dict[str, Any]) -> Dict[str, Any]:
        """Return a shallow-copied, gently semanticized version of the event.
        Context (episodic) features are attenuated as a function of age and repetition.
        This is neutral unless semanticization gain > 0.
        """
        pol = self._semanticization
        g = float(pol.get('gain', 0.0))
        if g == 0.0:
            return dict(e)
        age = float(e.get('tag_age', 0))
        reps = float(e.get('repeat_count', e.get('recurrence', 0)))
        # Build a sublinear driver from age and repetition
        driver = math.log1p(max(0.0, age)) * 0.5 + math.log1p(max(0.0, reps)) * 0.5
        # Semanticization factor in [0, max_bleach]
        f = 1.0 - math.exp(-g * driver)
        f = max(0.0, min(float(pol.get('max_bleach', MAX_BLEACH_COEFFICIENT)), f))
        out = dict(e)
        # Attenuate episodic context fields; preserve identifiers and scores
        for k in ('timing', 'duration', 'novelty'):
            if k in out and isinstance(out[k], (int, float)):
                out[k] = float(out[k]) * (1.0 - f)
        # Track context strength for diagnostics
        ctx0 = float(e.get('episodic_context_strength', 1.0))
        out['episodic_context_strength'] = max(0.0, ctx0 * (1.0 - f))
        out['semanticized'] = True
        out['semanticize_factor'] = f
        return out

    def set_thresholds(self, low: Optional[float] = None, high: Optional[float] = None) -> None:
        if low is not None:
            self.low_salience_threshold = float(low)
        if high is not None:
            self.high_salience_threshold = float(high)

    def set_similarity_policy(
        self,
        *,
        threshold: Optional[float] = None,
        weights: Optional[Dict[str, float]] = None,
        require_same_modality: Optional[bool] = None,
    ) -> None:
        if threshold is not None:
            self.similarity_threshold = float(threshold)
        if weights is not None:
            self.similarity_weights = weights.copy()
        if require_same_modality is not None:
            self.require_same_modality = bool(require_same_modality)

    def match_patterns(self, events: List[Dict[str, Any]], threshold: Optional[float] = None, return_scores: bool = False):
        matched: List[Dict[str, Any]] = []
        unmatched: List[Dict[str, Any]] = []
        scores: List[float] = []
        thr = self.similarity_threshold if threshold is None else float(threshold)
        for event in events:
            max_sim = self.max_similarity(event)
            scores.append(max_sim)
            if max_sim > thr:
                event_copy = event.copy()
                event_copy['recurrence'] = 1
                matched.append(event_copy)
            else:
                unmatched.append(event)
        if return_scores:
            return matched, unmatched, scores
        return matched, unmatched

    def prune_old_memory(self, min_salience=DEFAULT_MIN_SALIENCE_FOR_CLEANUP):
        # Only remove the oldest event below min_salience (if any)
        for idx, e in enumerate(self.short_term):
            if e.get('salience', 0) < min_salience:
                self.short_term.rotate(-idx)
                self.short_term.popleft()
                self.short_term.rotate(idx)
                break

    @property
    def long_term(self):
        # If no long-term store linked here, return empty dict by default
        return {}

    def tick_decay(self, memory_prune_threshold=None, *, stress: float | None = None, volatility: float | None = None, k_stress: float = 0.0, k_vol: float = 0.0):
        """
        Increment tag_age and apply exponential decay to each event's salience.
        Optionally prune events below memory_prune_threshold.
        Optional context modulation: if stress/volatility provided, decay_rate is
        multiplied by (1 + k_stress*stress + k_vol*volatility), clipped to [0.5, 2.0].
        """
        mod = 1.0
        if stress is not None or volatility is not None:
            s = float(stress) if stress is not None else 0.0
            v = float(volatility) if volatility is not None else 0.0
            mod = 1.0 + float(k_stress) * s + float(k_vol) * v
            mod = max(MODULATION_CLIP_MIN, min(MODULATION_CLIP_MAX, mod))
        for event in list(self.short_term):
            event['tag_age'] = event.get('tag_age', 0) + 1
            base_rate = event.get('decay_rate', math.log(2)/2000)
            rate = base_rate * mod
            event['salience'] *= math.exp(-rate)
        # Prune if threshold specified
        if memory_prune_threshold is not None:
            self.short_term = deque(
                [e for e in self.short_term if e.get('salience', 0) >= memory_prune_threshold],
                maxlen=self.short_term.maxlen
            )
        # Advance internal tick counter
        self._tick += 1

    def store_events(self, tagged_events):
        for raw_event in tagged_events:
            event = self._prepare_event_for_storage(raw_event)
            self.short_term.append(event)
            self._run_post_store_hook(event)

    def _prepare_event_for_storage(self, event: Dict[str, Any]) -> Dict[str, Any]:
        event = self._apply_pre_store_hook(event)
        self._coerce_numeric_fields(event)
        total_enc_mult = self._encoding_multiplier(event)
        self._ensure_identifier(event)
        self._apply_salience_scaling(event, total_enc_mult)
        self._apply_decay_schedule(event)
        return event

    def _apply_pre_store_hook(self, event: Dict[str, Any]) -> Dict[str, Any]:
        if self.pre_store_hook is None:
            return event
        try:
            return self.pre_store_hook(event) or event
        except Exception as hook_err:
            event_id = event.get('id', '<unknown>') if isinstance(event, dict) else '<non-dict>'
            logger.warning("pre_store_hook failed for event %s: %s", event_id, hook_err, exc_info=hook_err)
            return event

    def _coerce_numeric_fields(self, event: Dict[str, Any]) -> None:
        for k in ('duration', 'intensity', 'novelty', 'timing', 'prioritization_score', 'salience'):
            if k in event:
                try:
                    event[k] = float(event[k])
                except (ValueError, TypeError):
                    pass

    def _encoding_multiplier(self, event: Dict[str, Any]) -> float:
        valence        = float(event.get('valence', 0.0))
        arousal        = float(event.get('arousal', 0.0))           # 0..1 if provided
        meaningfulness = float(event.get('meaningfulness', 0.0))    # 0..1 if provided
        color_richness = float(event.get('color_richness', 0.0))    # 0..1 if provided
        exposure_mode  = str(event.get('exposure_mode', '2d'))
        c = self.encoding_coeffs
        enc_mult = (
            1.0
            + abs(valence)    * float(c.get('c_valence', 0.0))
            + arousal         * float(c.get('c_arousal', 0.0))
            + meaningfulness  * float(c.get('c_meaning', 0.0))
            + color_richness  * float(c.get('c_color', 0.0))
        )
        enc_mult = max(0.0, enc_mult)
        exp_mult = float(self.exposure_multipliers.get(exposure_mode, 1.0))
        return enc_mult * exp_mult

    def _ensure_identifier(self, event: Dict[str, Any]) -> None:
        if 'id' not in event or event.get('id') is None:
            event['id'] = f"evt_{self._next_id}"
            self._next_id += 1

    def _apply_salience_scaling(self, event: Dict[str, Any], total_enc_mult: float) -> None:
        base_initial_salience = float(event.get('initial_salience', event.get('salience', 0.0)))
        base_salience = float(event.get('salience', base_initial_salience))
        s0 = base_initial_salience * total_enc_mult
        event['initial_salience'] = s0
        event['salience'] = base_salience * total_enc_mult

    def _apply_decay_schedule(self, event: Dict[str, Any]) -> None:
        jitter = random.uniform(DECAY_JITTER_MIN, DECAY_JITTER_MAX)
        dyn_low = min(max(self.low_salience_threshold + jitter, 0), 1)
        dyn_high = min(max(self.high_salience_threshold + jitter, 0), 1)
        s0 = float(event.get('initial_salience', event.get('salience', 0.0)))
        if s0 < dyn_low:
            half_life = random.uniform(HALF_LIFE_LOW_SALIENCE_MIN, HALF_LIFE_LOW_SALIENCE_MAX)
        elif s0 > dyn_high:
            half_life = random.uniform(HALF_LIFE_HIGH_SALIENCE_MIN, HALF_LIFE_HIGH_SALIENCE_MAX)
        else:
            half_life = random.uniform(HALF_LIFE_MID_SALIENCE_MIN, HALF_LIFE_MID_SALIENCE_MAX)
        rep = float(event.get('repeat_count', 0.0))
        spacing_gain = float(self.encoding_coeffs.get('spacing_gain', 0.0))
        if spacing_gain != 0.0 and rep > 0.0:
            half_life *= (1.0 + spacing_gain * math.log1p(rep))
        event['dynamic_low_salience_threshold'] = dyn_low
        event['dynamic_high_salience_threshold'] = dyn_high
        event['half_life'] = round(half_life, 4)
        event['decay_rate'] = math.log(2) / half_life
        event['tag_age'] = event.get('tag_age', 0)

    def _run_post_store_hook(self, event: Dict[str, Any]) -> None:
        if self.post_store_hook is None:
            return
        try:
            self.post_store_hook(event)
        except Exception as hook_err:
            event_id = event.get('id', '<unknown>') if isinstance(event, dict) else '<unknown>'
            logger.warning("post_store_hook failed for event %s: %s", event_id, hook_err, exc_info=hook_err)

    def consolidate_to(
        self,
        long_term_storage: 'LongTermStorage',
        threshold: float = DEFAULT_CONSOLIDATION_THRESHOLD,
        boost_rate: float = DEFAULT_CONSOLIDATION_BOOST_RATE,
        transform: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
        deep_copy: bool = False,
        once_per_tick: bool = False,
    ) -> None:
        """Boost and move high-salience events to long-term storage.
        If `transform` is provided, apply it before storing.
        """
        for event in list(self.short_term):
            init = event.get('initial_salience', event.get('salience', 0))
            # Optional per-tick boost guard and skip-boost-if-already-above-threshold
            if not (once_per_tick and event.get('_last_boost_tick') == self._tick):
                if event.get('salience', 0) < threshold:
                    event['salience'] = event.get('salience', 0) + boost_rate * init
                    event['_last_boost_tick'] = self._tick
            if event.get('salience', 0) >= threshold:
                to_store = copy.deepcopy(event) if deep_copy else dict(event)
                if transform is not None:
                    try:
                        to_store = transform(to_store) or to_store
                    except Exception as transform_err:
                        event_id = to_store.get('id', '<unknown>') if isinstance(to_store, dict) else '<unknown>'
                        logger.warning("consolidate_to transform failed for event %s: %s", event_id, transform_err, exc_info=transform_err)
                else:
                    pol = getattr(self, '_semanticization', None)
                    if pol and pol.get('auto', False):
                        # Only semanticize if event meets minimal age/repetition criteria
                        min_age = int(pol.get('min_age', 0))
                        min_reps = int(pol.get('min_repeats', 0))
                        age = int(to_store.get('tag_age', 0))
                        reps = int(to_store.get('repeat_count', to_store.get('recurrence', 0)))
                        if age >= min_age and reps >= min_reps:
                            try:
                                to_store = self._semanticize_event(to_store)
                            except Exception as sem_err:
                                event_id = to_store.get('id', '<unknown>') if isinstance(to_store, dict) else '<unknown>'
                                logger.warning("Semanticization failed for event %s: %s", event_id, sem_err, exc_info=sem_err)
                long_term_storage.store(to_store)
                try:
                    self.short_term.remove(event)
                except ValueError:
                    pass

    def cleanup_low_salience(self, min_salience=DEFAULT_MIN_SALIENCE_FOR_CLEANUP):
        """
        Remove events below min salience threshold.
        """
        self.short_term = deque(
            [e for e in self.short_term if e.get('salience', 0) >= min_salience],
            maxlen=self.short_term.maxlen
        )

    def ensure_capacity(self, extra: int = 0, min_salience: float = DEFAULT_MIN_SALIENCE_FOR_CLEANUP, *, strategy: str | None = None, w_salience: float = DEFAULT_CAPACITY_WEIGHT_SALIENCE, w_recency: float = DEFAULT_CAPACITY_WEIGHT_RECENCY) -> None:
        need = max(0, (len(self.short_term) + extra) - self.short_term.maxlen)
        if need <= 0:
            return
        items = list(self.short_term)
        if strategy == 'soft_lru':
            def score(e):
                s = float(e.get('salience', 0.0))
                age = float(e.get('tag_age', 0))
                rec = math.exp(-age / max(1e-6, float(self.recency_tau)))
                return w_salience * s + w_recency * rec
            items.sort(key=score, reverse=True)
        else:
            items.sort(key=lambda e: e.get('salience', 0), reverse=True)
        kept = [e for e in items if e.get('salience', 0) >= min_salience]
        kept = kept[: max(0, self.short_term.maxlen - extra)]
        self.short_term.clear()
        for e in kept:
            self.short_term.append(e)

    def get_stats(self) -> Dict[str, float]:
        n = len(self.short_term)
        if n == 0:
            return {'count': 0, 'avg_salience': 0.0, 'max_salience': 0.0, 'min_salience': 0.0}
        sal = [e.get('salience', 0.0) for e in self.short_term]
        return {
            'count': float(n),
            'avg_salience': float(sum(sal) / n),
            'max_salience': float(max(sal)),
            'min_salience': float(min(sal)),
        }

    def snapshot(self) -> List[Dict[str, Any]]:
        return [e.copy() for e in self.short_term]

    def max_similarity(self, event: Dict[str, Any]) -> float:
        """
        Calculate max similarity to any event in short-term memory.
        """
        if not self.short_term:
            return 0.0
        sims = [self._event_similarity(event, p) for p in self.short_term]
        return max(sims)

    def _event_similarity(self, e1: Dict[str, Any], e2: Dict[str, Any]) -> float:
        if self.require_same_modality and (e1.get('modality') != e2.get('modality')):
            return 0.0
        weights = self.similarity_weights
        sim = 0.0

        dur_diff = abs(e1.get('duration', 0) - e2.get('duration', 0))
        dur_sim = max(0.0, 1 - dur_diff / 10)
        sim += weights['duration'] * dur_sim

        int_diff = abs(e1.get('intensity', 0) - e2.get('intensity', 0))
        int_sim = max(0.0, 1 - int_diff)
        sim += weights['intensity'] * int_sim

        nov_diff = abs(e1.get('novelty', 0) - e2.get('novelty', 0))
        nov_sim = max(0.0, 1 - nov_diff)
        sim += weights['novelty'] * nov_sim

        tim_diff = abs(e1.get('timing', 0) - e2.get('timing', 0))
        tim_sim = max(0.0, 1 - tim_diff)
        sim += weights['timing'] * tim_sim

        pri_diff = abs(e1.get('prioritization_score', 0) - e2.get('prioritization_score', 0))
        pri_sim = max(0.0, 1 - pri_diff)
        sim += weights['prioritization_score'] * pri_sim

        # Recency similarity (new, optional via weight)
        age = e2.get('tag_age', 0)
        try:
            rec_sim = math.exp(-float(age) / max(1e-6, float(self.recency_tau)))
        except (ValueError, TypeError, OverflowError):
            rec_sim = 0.0
        sim += weights.get('recency', 0.0) * rec_sim

        return max(0.0, min(1.0, sim))

    def replay_salient(self, top_k: int = 10, min_salience: float = 0.0, unique: bool = True) -> List[Dict[str, Any]]:
        items = [e for e in self.short_term if e.get('salience', 0) >= min_salience]
        items.sort(key=lambda e: e.get('salience', 0), reverse=True)
        if unique:
            seen = set()
            uniq = []
            for e in items:
                eid = e.get('id')
                if eid is None or eid not in seen:
                    uniq.append(e)
                    if eid is not None:
                        seen.add(eid)
            items = uniq
        return items[:max(0, top_k)]

    # Convenience: sizes
    def __len__(self):
        return len(self.short_term)

    def size(self):
        return len(self.short_term)

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

    # Convenience: sizes
    def __len__(self):
        return len(self.long_term)

    def size(self):
        return len(self.long_term)

    def snapshot(self) -> List[Dict[str, Any]]:
        return [dict(v) for v in self.long_term.values()]

    def clear(self) -> None:
        self.long_term.clear()
