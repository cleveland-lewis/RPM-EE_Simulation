# RPM-EE v1.1.0 Simulation

This directory contains the implementation of the Recursive Predictive Modeling with Emotional Encoding (RPM-EE) simulation architecture - a cognitive system that models sensor-to-action processing with emotional encoding, memory replay, and adaptive behavior.

## Architecture Overview

The RPM-EE system implements a complete cognitive loop:

**Sensors → Events → Memory → Simulations → Emotions → Replay → Actions → Feedback**

### Core Components

1. **SensoryInputSystem** (`sensory.py`) - Generates multi-modal sensory inputs
   - Five sensory channels: vision, hearing, touch, smell, taste
   - State-aware (awake, fatigued, asleep)
   - Intensity and duration modeling

2. **SalienceTagger** (`salience.py`) - Converts raw sensory data to tagged events
   - Event ID and timestamp generation
   - Emotion assignment (valence, category)
   - Novelty calculation
   - Prioritization scoring (0-10 scale)

3. **MemoryStore** (`memory.py`) - Pattern matching and memory management
   - Short-term memory (deque with max 1000 events)
   - Long-term memory (dict, for future consolidation)
   - Pattern similarity matching
   - Memory pruning

4. **RecursivePredictiveModeler** (`rpm.py`) - Generates predictive simulations
   - Slot-based simulation structure (agent, emotion, action, result)
   - Plausibility calculation
   - Emotional outcome prediction
   - Reward distortion bias

5. **EmotionalEncoder** (`emotion.py`) - Encodes simulations with emotional weights
   - Affect feedback calculation
   - Replay weight adjustment
   - Emotional fatigue tracking

6. **ReplayModeArbitrator** (`replay.py`) - Selects cognitive mode
   - Four modes: problem_solving, soothing, pattern_search, rest
   - Based on stress, prediction error, emotion volatility
   - Mode damping to prevent rapid switching

7. **ActionSystem** (`action.py`) - Action selection and execution
   - Mode-based simulation filtering
   - Weighted action selection
   - Action execution simulation
   - Feedback generation

8. **RPMEESimulation** (`simulation.py`) - Main orchestrator
   - Coordinates all subsystems
   - Tracks system state
   - Logs execution metrics

## Data Flow

```
1. Sensory Input Generation
   └─> Raw sensory data (modality, intensity, duration)

2. Event Tagging
   └─> Tagged events (ID, emotion, novelty, prioritization)

3. Memory Storage & Pattern Matching
   └─> Matched events (familiar) vs Unmatched events (novel)

4. Simulation Generation
   └─> Predictive simulations (action predictions, outcomes)

5. Emotional Encoding
   └─> Weighted simulations (replay weight, affect feedback)

6. Mode Selection
   └─> Current replay mode (soothing, problem_solving, etc.)

7. Action Selection & Execution
   └─> Selected action + outcome + feedback

8. State Update
   └─> Updated stress, prediction error, emotion volatility
```

## Event Schema

Each event has the following structure:
```python
{
    "id": "unique-uuid",
    "timestamp": "ISO-8601 UTC",
    "modality": "vision|hearing|touch|smell|taste",
    "state": "awake|fatigued|asleep",
    "novelty": 0.0-1.0,
    "emotion": {
        "valence": -1.0 to +1.0,
        "category": "joy|fear|disgust|anger|sadness|surprise|awe|neutral"
    },
    "recurrence": 0+,
    "timing": 0.0-1.0,
    "duration": 1+,
    "intensity": 0.0-1.0,
    "prioritization_score": 0.0-10.0
}
```

## Structure

- `src/` - Python source code
  - `main.py` - Entry point (runs 1000 episodes)
  - `simulation.py` - Main simulation orchestrator
  - `sensory.py` - Sensory input system
  - `salience.py` - Event tagging and prioritization
  - `memory.py` - Memory storage and pattern matching
  - `rpm.py` - Recursive predictive modeling
  - `emotion.py` - Emotional encoding
  - `replay.py` - Replay mode arbitration
  - `action.py` - Action selection and execution
  - `test_simulation.py` - Test script with statistics
- `config/` - YAML configuration for logging
- `logs/` - Output folder for logs and data
- `ISSUES_ANALYSIS.md` - Detailed analysis of all issues found

## How to Run

Basic simulation (1000 episodes):
```bash
python src/main.py
```

Test with statistics (100 episodes):
```bash
python src/test_simulation.py
```

## Implementation Status

### Completed ✅
- [x] Sensory input generation
- [x] Event tagging + prioritization
- [x] Pattern matching
- [x] Recursive simulation generation
- [x] Emotional encoding 
- [x] Replay mode arbitration
- [x] Action decision and execution
- [x] System state tracking
- [x] Basic testing infrastructure

### Remaining 🔨
- [ ] Long-term memory consolidation
- [ ] Replay selection mechanism
- [ ] Action-to-sensor feedback loop
- [ ] Structured logging to files
- [ ] Unit tests for individual components
- [ ] Visualization tools
- [ ] Configuration management

## Known Issues

See `ISSUES_ANALYSIS.md` for a complete analysis of identified issues, bugs, and planned improvements.

## Example Output

```
Episode 0 complete
Episode 10 complete
...
Simulation complete.

SIMULATION SUMMARY
==================
Total Episodes: 100
Total Events Generated: 430
Total Matched Events: 430
Match Rate: 100.0%

Action Distribution:
  observe: 37 (37.0%)
  approach: 19 (19.0%)
  explore: 18 (18.0%)
  ...

Final System State:
  Stress: 0.092
  Prediction Error: 0.165
  Emotion Volatility: 0.741
```

## Contributing

This is a research simulation. For issues or improvements, see the analysis in `ISSUES_ANALYSIS.md`.
