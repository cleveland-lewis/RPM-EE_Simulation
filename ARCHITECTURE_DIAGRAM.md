# RPM-EE Architecture Diagram

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         RPM-EE SIMULATION                            │
│                    (Recursive Predictive Modeling                    │
│                    with Emotional Encoding)                          │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│ CLOCK TICK   │──┐
└──────────────┘  │
                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│  1. SENSORY INPUT SYSTEM (sensory.py)                                │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  State Machine: AWAKE → FATIGUED → ASLEEP → (cycle)         │   │
│  │  Duration:      300      100        100                      │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  Channels:  Vision | Hearing | Touch | Smell | Taste                │
│  Output:    Multi-modal sensory packet {modality, intensity, dur}   │
└──────────────────────────────────────────────────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│  2. SALIENCE TAGGING (salience.py) ⚠️ SCHEMA ONLY                    │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Add: novelty, emotion{valence, category}, priority          │   │
│  │  Add: recurrence, timing                                     │   │
│  └──────────────────────────────────────────────────────────────┘   │
│  Output: Tagged events with emotional metadata                       │
└──────────────────────────────────────────────────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│  3. MEMORY SYSTEM (memory.py)                                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Short-term: Deque (max 1000 events)                         │   │
│  │  Long-term:  Dict (not yet used)                             │   │
│  │                                                               │   │
│  │  Pattern Matching: 6-feature weighted similarity             │   │
│  │    • Modality       (10%)                                    │   │
│  │    • Duration       (10%)                                    │   │
│  │    • Intensity      (10%)                                    │   │
│  │    • Emotion valence(30%) ← MOST IMPORTANT                  │   │
│  │    • Timing         (20%)                                    │   │
│  │    • Priority       (20%)                                    │   │
│  │                                                               │   │
│  │  Threshold: similarity > 0.8 → MATCHED                       │   │
│  │             similarity ≤ 0.8 → UNMATCHED                     │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
                  │
           ┌──────┴──────┐
           ▼             ▼
      MATCHED       UNMATCHED
      EVENTS         EVENTS
           │             │
           │             └─→ (stored but not simulated)
           ▼
┌──────────────────────────────────────────────────────────────────────┐
│  4. RECURSIVE PREDICTIVE MODELER (rpm.py)                            │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Slot Structure: [AGENT, EMOTION, ACTION, RESULT]           │   │
│  │                                                               │   │
│  │  For each matched event:                                     │   │
│  │    • Predict action    (approach/withdraw/explore/recoil)    │   │
│  │    • Predict result    (positive/negative/neutral outcome)   │   │
│  │    • Compute plausibility  (0.0-1.0)                        │   │
│  │    • Estimate emotion      (valence-based)                  │   │
│  │    • Calculate distortion  (emotional bias measure)         │   │
│  │                                                               │   │
│  │  Distortion = max(0, valence - plausibility)                │   │
│  │  (High emotion + Low realism = High distortion)             │   │
│  └──────────────────────────────────────────────────────────────┘   │
│  Output: List of simulations with predictions                        │
└──────────────────────────────────────────────────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│  5. EMOTIONAL ENCODER (emotion.py)                                   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Emotion Intensity = |emotional_prediction|                  │   │
│  │                                                               │   │
│  │  Affect Feedback:                                            │   │
│  │    IF distortion > 0.4 AND intensity > 0.6 → +0.6           │   │
│  │    ELSE IF intensity > 0.5              → +0.3              │   │
│  │    ELSE IF intensity > 0.2              → +0.1              │   │
│  │    ELSE                                  → -0.1              │   │
│  │                                                               │   │
│  │  Replay Weight = base_weight + affect_feedback               │   │
│  │                                                               │   │
│  │  Replay Fatigue:                                             │   │
│  │    IF replay_count > 3 → weight *= 0.5, set fatigue_flag   │   │
│  │                                                               │   │
│  └──────────────────────────────────────────────────────────────┘   │
│  Output: Simulations with adjusted replay weights                    │
└──────────────────────────────────────────────────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│  6. REPLAY MODE ARBITRATOR (replay.py) ⚠️ NOT YET INTEGRATED         │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Mode Selection (priority order):                            │   │
│  │                                                               │   │
│  │    IF stress > 0.7              → SOOTHING                  │   │
│  │    ELSE IF prediction_error > 0.6 → PROBLEM_SOLVING         │   │
│  │    ELSE IF emotion_volatility > 0.5 → PATTERN_SEARCH        │   │
│  │    ELSE                           → REST                     │   │
│  │                                                               │   │
│  │  Mode Damping: Minimum duration = 5 cycles                  │   │
│  │                (prevents rapid switching)                    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│  Output: Selected operating mode                                     │
└──────────────────────────────────────────────────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│  7. ACTION SELECTION ⚠️ NOT YET IMPLEMENTED                          │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  (Future implementation)                                      │   │
│  │  • Filter simulations by mode                                │   │
│  │  • Weight by replay_weight                                   │   │
│  │  • Select action(s) to execute                               │   │
│  └──────────────────────────────────────────────────────────────┘   │
│  Output: Action decisions                                            │
└──────────────────────────────────────────────────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│  8. LOGGING & OUTPUT                                                 │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Currently logs to memory:                                   │   │
│  │    • Clock tick                                              │   │
│  │    • System state (awake/fatigued/asleep)                   │   │
│  │    • Event count                                             │   │
│  │    • Simulation count                                        │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Data Object Transformations

```
Raw Sensory Input
├─ modality: str
├─ intensity: float
└─ duration: int
    │
    ▼ (Salience Tagging)
Tagged Event
├─ id: uuid
├─ modality: str
├─ intensity: float
├─ duration: int
├─ novelty: float ◄─── NEW
├─ emotion: {valence, category} ◄─── NEW
├─ recurrence: int ◄─── NEW
├─ timing: float ◄─── NEW
└─ prioritization_score: float ◄─── NEW
    │
    ▼ (Memory Matching)
Matched Event (same structure + memory context)
    │
    ▼ (Simulation Generation)
Simulation
├─ id: uuid
├─ source_event_id: str
├─ agent: str
├─ emotion: dict
├─ action: str ◄─── PREDICTED
├─ result: str ◄─── PREDICTED
├─ plausibility: float ◄─── COMPUTED
├─ emotional_prediction: float ◄─── ESTIMATED
├─ reward_distortion: float ◄─── COMPUTED
└─ replay_weight: float (default 1.0)
    │
    ▼ (Emotional Encoding)
Encoded Simulation (+ feedback)
├─ ... (all above fields)
├─ emotion_intensity: float ◄─── NEW
├─ affect_feedback: float ◄─── NEW
├─ replay_weight: float (adjusted) ◄─── MODIFIED
└─ fatigue_flag: bool ◄─── NEW
```

---

## Component Interaction Matrix

```
┌──────────┬─────────┬─────────┬────────┬─────┬─────────┬─────────┬────────┐
│          │ Sensory │ Salience│ Memory │ RPM │ Emotion │ Replay  │ Action │
│          │ Input   │ Tagger  │ Store  │     │ Encoder │ Arbiter │ Select │
├──────────┼─────────┼─────────┼────────┼─────┼─────────┼─────────┼────────┤
│ Sensory  │    -    │    ✓    │        │     │         │         │        │
│ Input    │         │ (sends) │        │     │         │         │        │
├──────────┼─────────┼─────────┼────────┼─────┼─────────┼─────────┼────────┤
│ Salience │         │    -    │   ✓    │     │         │         │        │
│ Tagger   │         │         │(sends) │     │         │         │        │
├──────────┼─────────┼─────────┼────────┼─────┼─────────┼─────────┼────────┤
│ Memory   │         │         │   -    │  ✓  │         │         │        │
│ Store    │         │         │        │(send│         │         │        │
│          │         │         │        │matched)      │         │        │
├──────────┼─────────┼─────────┼────────┼─────┼─────────┼─────────┼────────┤
│ RPM      │         │         │        │  -  │    ✓    │         │        │
│          │         │         │        │     │ (sends) │         │        │
├──────────┼─────────┼─────────┼────────┼─────┼─────────┼─────────┼────────┤
│ Emotion  │         │         │        │     │    -    │    ✓    │        │
│ Encoder  │         │         │        │     │         │ (sends) │        │
├──────────┼─────────┼─────────┼────────┼─────┼─────────┼─────────┼────────┤
│ Replay   │         │         │        │     │         │    -    │   ✓    │
│ Arbiter  │         │         │        │     │         │         │ (mode) │
├──────────┼─────────┼─────────┼────────┼─────┼─────────┼─────────┼────────┤
│ Action   │         │         │        │     │         │         │   -    │
│ Select   │         │         │        │     │         │         │        │
└──────────┴─────────┴─────────┴────────┴─────┴─────────┴─────────┴────────┘

Legend:
  ✓ = Data flow connection
  - = Self (diagonal)
  (blank) = No direct connection
```

---

## Emotional Weighting System

```
                    EMOTIONAL IMPACT ON REPLAY
                    
High Distortion     ┌─────────────────────────┐
(Wishful/Fearful)   │  STRONGLY AMPLIFIED     │
                    │  (+0.6 boost)           │
                    │                         │
                    │  "Emotional fantasies"  │
                    └─────────────────────────┘
                              ▲
                              │
High Intensity      ┌─────────┴───────────────┐
(Strong Emotion)    │  AMPLIFIED              │
                    │  (+0.3 boost)           │
                    │                         │
                    │  "Vivid memories"       │
                    └─────────────────────────┘
                              ▲
                              │
Medium Intensity    ┌─────────┴───────────────┐
(Moderate Emotion)  │  SLIGHTLY BOOSTED       │
                    │  (+0.1 boost)           │
                    │                         │
                    │  "Background thoughts"  │
                    └─────────────────────────┘
                              ▲
                              │
Low Intensity       ┌─────────┴───────────────┐
(Weak Emotion)      │  SUPPRESSED             │
                    │  (-0.1 penalty)         │
                    │                         │
                    │  "Forgotten quickly"    │
                    └─────────────────────────┘

                    REPLAY FATIGUE
                    
Replay Count:  1    2    3  │  4    5    6
Weight:       1.0  1.0  1.0 │ 0.5  0.5  0.5
                            │
                         Fatigue
                        Threshold
                        
"After 3 replays, habituation reduces salience by 50%"
```

---

## State Machine Diagram

```
SENSORY SYSTEM STATES

    ┌──────────┐  300 ticks  ┌────────────┐  100 ticks  ┌─────────┐
    │  AWAKE   │────────────▶│  FATIGUED  │────────────▶│  ASLEEP │
    └──────────┘             └────────────┘             └─────────┘
         ▲                                                     │
         │                       100 ticks                     │
         └─────────────────────────────────────────────────────┘

State Effects:
  AWAKE:    • Full sensory input (vision: 0-3, hearing: 0-2, touch: 1-2)
            • High intensity (0.1-1.0)
            
  FATIGUED: • (Same as AWAKE in current implementation)
            • Potential for reduced processing in future versions
            
  ASLEEP:   • Minimal sensory input (vision: suppressed)
            • Low intensity (0.0-0.3)
            • Hearing still partially active (0.0-0.3)
            • Touch minimal (0.0-0.2)
            
Total Cycle: 500 ticks (≈8.3 hours if 1 tick = 1 minute)


REPLAY MODE STATES

┌─────────────────┐         stress > 0.7          ┌──────────────┐
│ PROBLEM_SOLVING │◀───────────────────────────────│   SOOTHING   │
└─────────────────┘                                └──────────────┘
         ▲                                                │
         │                                                │
         │ prediction_error > 0.6                         │
         │                                                ▼
         │                                         emotion_volatility > 0.5
         │                                                │
         │                                                │
┌────────┴────────┐                                ┌─────┴────────┐
│      REST       │───────────────────────────────▶│PATTERN_SEARCH│
└─────────────────┘         default                └──────────────┘

Mode Characteristics:
  PROBLEM_SOLVING: • High prediction error → need to resolve uncertainty
                   • Focused replay on failed predictions
                   
  SOOTHING:        • High stress → need emotional regulation
                   • Replay positive/calming simulations
                   
  PATTERN_SEARCH:  • High emotion volatility → unstable state
                   • Search for patterns to explain emotional shifts
                   
  REST:            • Default low-activation state
                   • Consolidation and random replay

Minimum Duration: 5 cycles per mode (damping prevents thrashing)
```

---

## Memory Architecture

```
SHORT-TERM MEMORY (Working Memory)
┌────────────────────────────────────────────┐
│  Deque (FIFO with capacity limit)          │
│  Max Capacity: 1000 events                 │
│                                             │
│  [Event_999] ← newest                      │
│  [Event_998]                               │
│  [Event_997]                               │
│      ...                                   │
│  [Event_001]                               │
│  [Event_000] ← oldest (removed if full)    │
│                                             │
│  Pruning: Remove if priority ≤ 0.3         │
└────────────────────────────────────────────┘
                  │
                  ▼ (Future: consolidation)
LONG-TERM MEMORY (Not Yet Implemented)
┌────────────────────────────────────────────┐
│  Dict (key-value store)                    │
│  Capacity: Unlimited                       │
│                                             │
│  Storage criteria: (to be defined)         │
│    • High priority events                  │
│    • Frequently matched patterns           │
│    • High emotional intensity              │
│                                             │
│  Decay mechanism: (to be defined)          │
└────────────────────────────────────────────┘
```

---

## Similarity Calculation Formula

```
Similarity(Event1, Event2) = 
    
    0.10 × Modality_Match                 (binary: 1.0 or 0.0)
  + 0.10 × (1 - |Δ Duration| / 10)        (normalized difference)
  + 0.10 × (1 - |Δ Intensity|)            (absolute difference)
  + 0.30 × (1 - |Δ Valence|)              (absolute difference) ★
  + 0.20 × (1 - |Δ Timing|)               (absolute difference)
  + 0.20 × (1 - |Δ Priority| / 10)        (normalized difference)
    
Result: 0.0 to 1.0

★ Emotion valence is the most influential factor (30% weight)

Example:
  Event A: {modality: vision, duration: 5, intensity: 0.8, valence: 0.6, ...}
  Event B: {modality: vision, duration: 6, intensity: 0.7, valence: 0.7, ...}
  
  Similarity = 0.1×1.0 + 0.1×0.9 + 0.1×0.9 + 0.3×0.9 + ... ≈ 0.85
  
  → MATCHED (threshold = 0.8)
```

---

## Code Template Status

```
┌──────────────────────────────────────────────────────────────┐
│  ⚠️ ALL FILES ARE IN TEMPLATE STATE                          │
│                                                               │
│  Current Structure:                                          │
│    file_code = """                                           │
│        actual code here                                      │
│    """                                                       │
│                                                               │
│  Required Transformation:                                    │
│    Remove string wrapper                                     │
│    → Direct Python code                                      │
│                                                               │
│  Status: NOT EXECUTABLE                                      │
└──────────────────────────────────────────────────────────────┘
```

---

*This diagram provides a visual reference for the RPM-EE architecture.*  
*Refer to CODEBASE_ANALYSIS.md for detailed explanations.*
