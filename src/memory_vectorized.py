"""
Vectorized Memory Store with Interference-Based Decay.

Drop-in replacement for MemoryStore using NumPy + optional Numba JIT for
similarity computation. Replaces the prior uniform exponential decay
  prio *= (1 - decay_rate)
with an interference-based decay model in which incoming stimuli
selectively suppress memory traces according to their cosine similarity,
implementing retroactive interference (Bower, 1981; Anderson & Neely, 1996).

Interference-based decay:
    For each stored event i and each incoming event j:
        cosine_ij = (x_i · x_j) / (‖x_i‖ · ‖x_j‖)
        interference_i = max_j { (cosine_ij + 1) / 2 }   ∈ [0, 1]
        decay_factor_i = max(0, 1 - decay_rate · (1 + interference_i))

    Highly similar incoming events (interference → 1) suppress existing traces
    more strongly than dissimilar events (interference → 0), which experience
    only base-rate decay.  This produces the localized, asynchronous trace
    competition characteristic of proactive and retroactive interference.

References
----------
- Bower, G. H. (1981). Mood and memory. American Psychologist, 36(2), 129-148.
- Anderson, M. C., & Neely, J. H. (1996). Interference and inhibition in
  memory retrieval. In Memory. Academic Press.
- Numba JIT: first call incurs ~50ms compilation; subsequent calls are fast.

Feature flag: RPMEESimulation(use_vectorized_memory=True).
"""

from collections import deque

import numpy as np

try:
    from numba import njit

    _NUMBA_AVAILABLE = True
except ImportError:
    _NUMBA_AVAILABLE = False


# Feature-vector indices that are on a raw (non-[0,1]) scale and need
# normalizing before they can contribute to a [0,1] similarity score.
_IDX_DURATION = 1
_IDX_PRIORITIZATION = 5
_NORMALIZE_BY = 10.0

# ---------------------------------------------------------------------------
# Numba-accelerated similarity kernel
# ---------------------------------------------------------------------------

if _NUMBA_AVAILABLE:

    @njit(cache=True)
    def _batch_similarity_numba(
        query: np.ndarray,  # shape (6,) float32
        memory: np.ndarray,  # shape (N, 6) float32
        weights: np.ndarray,  # shape (6,) float32
    ) -> np.ndarray:
        """Weighted cosine-like similarity between query and all memory rows."""
        n_rows = memory.shape[0]
        scores = np.empty(n_rows, dtype=np.float32)
        for i in range(n_rows):
            s = 0.0
            for j in range(6):
                diff = abs(query[j] - memory[i, j])
                if j in (_IDX_DURATION, _IDX_PRIORITIZATION):
                    diff = diff / _NORMALIZE_BY
                feat_sim = min(1.0, max(0.0, 1.0 - diff))
                s += weights[j] * feat_sim
            scores[i] = s
        return scores

else:

    def _batch_similarity_numba(query, memory, weights):
        """Compute batch similarity via plain NumPy when Numba is unavailable."""
        diffs = np.abs(query - memory)
        diffs[:, _IDX_DURATION] /= _NORMALIZE_BY
        diffs[:, _IDX_PRIORITIZATION] /= _NORMALIZE_BY
        feat_sims = np.clip(1.0 - diffs, 0.0, 1.0)
        return (feat_sims * weights).sum(axis=1).astype(np.float32)


# Feature weights matching MemoryStore._event_similarity
_WEIGHTS = np.array([0.1, 0.1, 0.1, 0.3, 0.2, 0.2], dtype=np.float32)

# Thresholds matching MemoryStore's semantics (see get_working_memory_load,
# match_patterns, prune_old_memory there)
_ACTIVE_PRIORITY_THRESHOLD = 0.5
_MATCH_SIMILARITY_THRESHOLD = 0.8
_PRUNE_PRIORITY_THRESHOLD = 0.3

# Modality encoding for vectorization
_MODALITY_MAP = {
    "vision": 0.0,
    "auditory": 0.25,
    "touch": 0.5,
    "proprioception": 0.75,
    "other": 1.0,
}


def _event_to_vector(event: dict) -> np.ndarray:
    """
    Convert an event dict to a float32 feature vector.

    Feature layout:
        [0] modality     (encoded 0-1)
        [1] duration     (raw, normalised by 10 in similarity kernel)
        [2] intensity    (0-1)
        [3] valence      (emotion valence, -1 to 1)
        [4] timing       (0-1)
        [5] prioritization_score (raw, normalised by 10 in similarity kernel)
    """
    modality_val = _MODALITY_MAP.get(event.get("modality", "other"), 1.0)
    return np.array(
        [
            modality_val,
            float(event.get("duration", 0.0)),
            float(event.get("intensity", 0.0)),
            float(event.get("emotion", {}).get("valence", 0.0)),
            float(event.get("timing", 0.0)),
            float(event.get("prioritization_score", 0.0)),
        ],
        dtype=np.float32,
    )


class VectorizedMemoryStore:
    """
    NumPy + Numba vectorized replacement for MemoryStore.

    Interface-compatible with MemoryStore (same public methods and attributes).

    Key difference from MemoryStore:
    - Similarity computation vectorised via NumPy / Numba kernel.
    - Decay is interference-based (cosine-similarity-weighted retroactive
      suppression) rather than a uniform multiplicative scalar.
    """

    def __init__(self, max_short_term: int = 1000):
        self.short_term: deque = deque(maxlen=max_short_term)
        self.long_term: dict = {}

        self._max_size = max_short_term
        self._vectors = np.zeros((max_short_term, 6), dtype=np.float32)
        self._prio_scores = np.zeros(max_short_term, dtype=np.float32)
        self._n = 0

        # Clinical preset parameters (matches MemoryStore API)
        self.capacity = 4  # Default WM capacity (Cowan 2001, 4±1 -- see src/presets.py)
        self.decay_rate = 0.01

    # ------------------------------------------------------------------
    # Public API (matches MemoryStore)
    # ------------------------------------------------------------------

    def store_events(self, tagged_events: list[dict]) -> None:
        """
        Store events and apply interference-based decay.

        Incoming events act as interference sources: stored events with high
        cosine similarity to any incoming event decay faster (retroactive
        interference). Dissimilar stored events experience only base decay.
        """
        if not tagged_events:
            return

        # Collect incoming feature vectors before insertion
        new_vectors = np.array([_event_to_vector(e) for e in tagged_events], dtype=np.float32)
        for event in tagged_events:
            self._insert(event)

        self._apply_decay(incoming=new_vectors)

    def get_working_memory_load(self) -> float:
        """Calculate working memory load based on capacity."""
        if self._n == 0:
            return 0.0
        active = int(np.sum(self._prio_scores[: self._n] > _ACTIVE_PRIORITY_THRESHOLD))
        return min(1.0, active / self.capacity) if self.capacity > 0 else 0.0

    def match_patterns(self, new_events: list[dict]) -> tuple[list[dict], list[dict]]:
        """Classify events as matched (weighted similarity > 0.8) or unmatched."""
        matched: list[dict] = []
        unmatched: list[dict] = []
        if self._n == 0:
            return matched, list(new_events)

        memory_slice = self._vectors[: self._n]
        for event in new_events:
            query = _event_to_vector(event)
            scores = _batch_similarity_numba(query, memory_slice, _WEIGHTS)
            if float(scores.max()) > _MATCH_SIMILARITY_THRESHOLD:
                matched.append(event)
                event["recurrence"] = 1
            else:
                unmatched.append(event)
        return matched, unmatched

    def prune_old_memory(self) -> None:
        """Remove events with prioritization_score ≤ 0.3."""
        if self._n == 0:
            return
        keep = self._prio_scores[: self._n] > _PRUNE_PRIORITY_THRESHOLD
        n_keep = int(keep.sum())
        self._vectors[:n_keep] = self._vectors[: self._n][keep]
        self._prio_scores[:n_keep] = self._prio_scores[: self._n][keep]
        self._n = n_keep

        surviving: deque = deque(maxlen=self.short_term.maxlen)
        for event in self.short_term:
            if event.get("prioritization_score", 0) > _PRUNE_PRIORITY_THRESHOLD:
                surviving.append(event)
        self.short_term = surviving

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _insert(self, event: dict) -> None:
        """Insert one event into the ring buffer."""
        if self._n < self._max_size:
            idx = self._n
            self._n += 1
        else:
            self._vectors[: self._max_size - 1] = self._vectors[1 : self._max_size]
            self._prio_scores[: self._max_size - 1] = self._prio_scores[1 : self._max_size]
            idx = self._max_size - 1

        self._vectors[idx] = _event_to_vector(event)
        self._prio_scores[idx] = float(event.get("prioritization_score", 0.0))
        self.short_term.append(event)

    def _apply_decay(self, incoming: np.ndarray = None) -> None:
        """
        Apply interference-based decay to stored prioritization scores.

        Algorithm:
          1. Compute cosine similarity between each stored event and each
             incoming event: cosine ∈ [-1, 1].
          2. Rescale to [0, 1]: interference = (cosine + 1) / 2.
          3. Take the maximum interference from any incoming event per stored item.
          4. Decay factor per item: max(0, 1 - decay_rate · (1 + interference))
             → high similarity ⟹ faster decay (retroactive interference).
             → low similarity ⟹ near-base-rate decay.

        When called without arguments (e.g., for direct timing tests),
        falls back to uniform base-rate decay for backward compatibility.

        Args
        ----
        incoming: float32 array of shape (M, 6) — feature vectors of
                  newly stored events (the interference sources).
        """
        if self._n == 0:
            return

        if incoming is None or incoming.shape[0] == 0:
            # Fallback: uniform base-rate decay (no interference source)
            self._prio_scores[: self._n] *= 1.0 - self.decay_rate
        else:
            memory_slice = self._vectors[: self._n]  # (N, 6)

            # L2-normalise for cosine similarity (add eps to avoid /0)
            mem_norms = np.linalg.norm(memory_slice, axis=1, keepdims=True) + 1e-8  # (N, 1)
            inc_norms = np.linalg.norm(incoming, axis=1, keepdims=True) + 1e-8  # (M, 1)

            mem_unit = memory_slice / mem_norms  # (N, 6)
            inc_unit = incoming / inc_norms  # (M, 6)

            cosines = mem_unit @ inc_unit.T  # (N, M)

            # Maximum interference per stored item across all incoming events
            max_cos = cosines.max(axis=1)  # (N,)
            interference = (max_cos + 1.0) / 2.0  # rescale [-1,1] → [0,1]

            # Per-item decay: base rate amplified by interference
            decay_factors = np.maximum(0.0, 1.0 - self.decay_rate * (1.0 + interference))
            self._prio_scores[: self._n] *= decay_factors

        # Sync dict items (for WM load calculation via event dicts)
        for i, event in enumerate(self.short_term):
            if i < self._n and "prioritization_score" in event:
                event["prioritization_score"] = float(self._prio_scores[i])
