# RPM-EE v1.1.0 Simulation

## Recursive Predictive Modeling with Emotional Encoding

A computational cognitive architecture simulating human-like mental simulation, memory consolidation, and emotional replay mechanisms. This framework models how emotions influence predictive processing, memory formation, and decision-making through recursive simulation and affective encoding.

---

## Table of Contents

1. [Overview](#overview)
2. [Theoretical Foundation](#theoretical-foundation)
3. [Architecture](#architecture)
4. [Installation](#installation)
5. [Usage](#usage)
6. [System Components](#system-components)
7. [Configuration](#configuration)
8. [Simulation Pipeline](#simulation-pipeline)
9. [Technical Specifications](#technical-specifications)
10. [Output and Logging](#output-and-logging)
11. [Development](#development)
12. [Troubleshooting](#troubleshooting)
13. [References](#references)

---

## Overview

**RPM-EE** (Recursive Predictive Modeling with Emotional Encoding) is a computational framework that explores the intersection of predictive processing, emotional tagging, and memory replay in cognitive systems. The simulation models:

- **Sensory Processing**: Multi-modal input generation across vision, hearing, touch, smell, and taste
- **Emotional Tagging**: Affective valence assignment to sensory events
- **Pattern Recognition**: Memory-based matching and novelty detection
- **Recursive Simulation**: Slot-based predictive modeling of future states
- **Emotional Encoding**: Affect-driven replay weight modulation
- **Memory Consolidation**: Short-term to long-term memory transfer with emotional prioritization

This architecture provides insights into how emotional states bias cognitive simulations, influence decision-making, and shape memory consolidation—processes central to human cognition, dreaming, and rumination.

---

## Theoretical Foundation

### Predictive Processing Framework

RPM-EE builds on the **predictive processing** theory of cognition, which posits that the brain constantly generates predictions about sensory input and updates internal models based on prediction errors. Key principles:

- **Active Inference**: The system generates internal simulations to minimize prediction error
- **Hierarchical Processing**: Multi-level representations from sensory input to abstract concepts
- **Precision Weighting**: Emotional salience modulates the weight given to different predictions

### Emotional Encoding Hypothesis

The simulation implements the hypothesis that emotions serve as meta-cognitive signals that:

1. **Prioritize Memory Storage**: High-emotion events receive preferential encoding
2. **Bias Replay Selection**: Emotional weight influences which memories are reactivated
3. **Modulate Learning Rates**: Affective valence adjusts prediction error sensitivity
4. **Enable Reward Distortion**: Positive emotions can bias simulations toward unrealistic optimism

### Slot-Based Mental Simulation

Drawing from cognitive science research on mental simulation, the system uses a **slot-filling architecture** with components:

- **Agent**: Who is performing the action (self/other)
- **Emotion**: Affective state associated with the simulation
- **Action**: Predicted behavior or response
- **Result**: Anticipated outcome or consequence

This structure mirrors how humans mentally simulate hypothetical scenarios during planning and rumination.

---

## Architecture

### High-Level System Flow

```
┌─────────────────┐
│ Sensory Input   │ → Multi-modal event generation
│ System          │    (vision, hearing, touch, etc.)
└────────┬────────┘
         ↓
┌─────────────────┐
│ Salience Tagger │ → Emotional valence assignment
│                 │    Novelty and priority scoring
└────────┬────────┘
         ↓
┌─────────────────┐
│ Memory Store    │ → Pattern matching
│                 │    Short-term/long-term storage
└────────┬────────┘
         ↓
┌─────────────────┐
│ Recursive       │ → Slot-based simulation generation
│ Predictive      │    Plausibility assessment
│ Modeler (RPM)   │    Reward distortion calculation
└────────┬────────┘
         ↓
┌─────────────────┐
│ Emotional       │ → Affect feedback loops
│ Encoder         │    Replay weight modulation
│                 │    Fatigue-based suppression
└────────┬────────┘
         ↓
┌─────────────────┐
│ Replay Mode     │ → Mode selection (problem-solving,
│ Arbitrator      │    soothing, pattern search, rest)
└────────┬────────┘
         ↓
┌─────────────────┐
│ Action Decision │ → Behavioral output (future work)
└─────────────────┘
```

---

## Installation

### Prerequisites

- **Python**: 3.7 or higher
- **Operating System**: Linux, macOS, or Windows
- **Dependencies**: Standard library only (no external packages required)

### Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/cleveland-lewis/RPM-EE_Simulation.git
   cd RPM-EE_Simulation
   ```

2. **Verify Directory Structure**
   ```bash
   ls -la
   # Should show: src/, config/, README.md
   ```

3. **Create Logs Directory** (if not present)
   ```bash
   mkdir -p logs
   ```

4. **Optional: Set Up Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

---

## Usage

### Basic Execution

Run the simulation with default parameters (1000 episodes):

```bash
python src/main.py
```

**Expected Output:**
```
Episode 0 complete
Episode 10 complete
Episode 20 complete
...
Episode 990 complete
Simulation complete.
```

### Custom Episode Count

Modify `src/main.py` to adjust simulation length:

```python
def main():
    sim = RPMEESimulation()
    sim.run(episodes=5000)  # Run 5000 episodes instead
```

### Monitoring Logs

The simulation generates logs in `logs/simulation.log`:

```bash
tail -f logs/simulation.log
```

---

## System Components

### 1. Sensory Input System (`sensory.py`)

**Purpose**: Simulates multi-modal sensory inputs across different conscious states.

**Key Features**:
- **State Transitions**: Cycles through `awake` (300 steps) → `fatigued` (100 steps) → `asleep` (100 steps)
- **Modality Channels**: Vision, hearing, touch, smell, taste
- **State-Dependent Input**: Sleep suppresses vision, reduces other modalities
- **Random Variation**: Stochastic intensity and duration for realistic variability

**Technical Details**:
```python
# Example vision input during awake state
{
    "modality": "vision",
    "intensity": 0.75,    # Range: 0.1-1.0
    "duration": 7         # Time steps: 1-10
}
```

**Parameters**:
- `clock`: Internal time counter
- `state`: Current conscious state
- `state_durations`: Time spent in each state before transition

---

### 2. Salience Tagger (`salience.py`)

**Purpose**: Assigns emotional valence and priority scores to sensory events.

**Tagging Schema**:
```json
{
  "id": "unique-id",
  "timestamp": "UTC time",
  "modality": "vision / touch / hearing / ...",
  "state": "awake / fatigued / asleep",
  "novelty": 0.0–1.0,
  "emotion": {
    "valence": -1.0 to +1.0,
    "category": "awe / disgust / joy / fear / ..."
  },
  "recurrence": 0,
  "timing": 0.0–1.0,
  "duration": 3,
  "intensity": 0.8,
  "prioritization_score": 0.0–10.0
}
```

**Key Mechanisms**:
- **Emotional Valence**: Assigns positive/negative affect based on intensity and modality
- **Novelty Detection**: Compares against recent history to identify unique events
- **Priority Scoring**: Multi-factor calculation combining emotion, novelty, and intensity

---

### 3. Memory Store (`memory.py`)

**Purpose**: Implements short-term and long-term memory with pattern matching.

**Memory Architecture**:
- **Short-Term Memory**: FIFO queue with 1000-event capacity
- **Long-Term Memory**: Dictionary-based persistent storage
- **Pattern Matching**: Cosine-similarity-based event comparison

**Similarity Calculation**:
```python
Similarity = weighted_sum([
    modality_match * 0.1,
    duration_similarity * 0.1,
    intensity_similarity * 0.1,
    emotion_valence_similarity * 0.3,
    timing_similarity * 0.2,
    prioritization_similarity * 0.2
])
```

**Matching Threshold**: Events with similarity > 0.8 are considered "matched" (familiar)

**Memory Pruning**: Events with `prioritization_score < 0.3` are periodically removed

---

### 4. Recursive Predictive Modeler (`rpm.py`)

**Purpose**: Generates slot-based mental simulations from matched events.

**Simulation Structure**:
```python
{
    "id": "uuid",
    "source_event_id": "event-uuid",
    "agent": "self",  # or "other"
    "emotion": {"valence": 0.6, "category": "joy"},
    "action": "approach",  # or "withdraw", "explore", "observe"
    "result": "positive outcome",  # or "negative", "neutral"
    "plausibility": 0.85,  # Physical realism score
    "emotional_prediction": 0.6,  # Expected emotional outcome
    "reward_distortion": 0.15,  # Bias toward wishful thinking
    "replay_weight": 1.0  # Initial replay priority
}
```

**Action Prediction Logic**:
- **Vision-based**: `approach` (positive valence) vs `withdraw` (negative)
- **Touch-based**: `explore` (positive) vs `recoil` (negative)
- **Default**: `observe`

**Plausibility Calculation**:
```python
plausibility = 1.0 - abs(intensity - 0.5)
```

**Reward Distortion**:
```python
distortion = max(0.0, emotional_valence - plausibility)
```
*Captures "wishful thinking" where high positive emotion exceeds realistic outcomes*

---

### 5. Emotional Encoder (`emotion.py`)

**Purpose**: Modulates replay weights based on emotional feedback and fatigue.

**Affect Feedback Loop**:
- **High distortion + High emotion** → `+0.6` replay boost (reinforces fantasies)
- **Moderate emotion** → `+0.3` replay boost
- **Low emotion** → `+0.1` replay boost
- **Very low emotion** → `-0.1` replay suppression

**Emotional Fatigue**:
- Tracks replay count per simulation ID
- After 3 replays, weight is halved (0.5x multiplier)
- Prevents obsessive rumination on single events

**Technical Implementation**:
```python
if simulation_replay_count > 3:
    replay_weight *= 0.5
    fatigue_flag = True
```

---

### 6. Replay Mode Arbitrator (`replay.py`)

**Purpose**: Selects cognitive mode based on system state.

**Modes**:
1. **Problem Solving**: High prediction error → generate action-oriented simulations
2. **Soothing**: High stress → replay comforting memories
3. **Pattern Search**: High emotion volatility → seek regularities in experience
4. **Rest**: Low arousal → minimal processing

**Mode Selection Logic**:
```python
if stress > 0.7:
    mode = "soothing"
elif prediction_error > 0.6:
    mode = "problem_solving"
elif emotion_volatility > 0.5:
    mode = "pattern_search"
else:
    mode = "rest"
```

**Damping Mechanism**: Prevents rapid mode switching (minimum 5 cycles per mode)

---

## Configuration

### Logging Configuration (`config/logging.yaml`)

```yaml
version: 1
disable_existing_loggers: False
formatters:
  simple:
    format: '%(asctime)s - %(levelname)s - %(message)s'
handlers:
  file:
    class: logging.FileHandler
    filename: logs/simulation.log
    formatter: simple
    level: INFO
root:
  level: INFO
  handlers: [file]
```

**Customization Options**:
- Change `filename` to redirect logs
- Adjust `level` to `DEBUG` for verbose output
- Add console handler for real-time monitoring

---

## Simulation Pipeline

### Step-by-Step Execution Flow

Each simulation step (`sim.step()`) executes the following sequence:

```
1. Update Clock
   └─> Increment internal time counter
   └─> Update sensory system state (awake/fatigued/asleep)

2. Generate Sensory Input
   └─> Create multi-modal input packet
   └─> State-dependent intensity and frequency

3. Tag with Salience
   └─> Assign emotional valence
   └─> Calculate novelty and priority

4. Store in Memory
   └─> Add to short-term memory queue
   └─> Pattern matching against existing events

5. Split Matched vs Unmatched
   └─> Matched (familiar) → Generate simulations
   └─> Unmatched (novel) → Store for future reference

6. Generate Slot-Based Simulations
   └─> Create agent-action-result triplets
   └─> Calculate plausibility and distortion

7. Emotionally Encode Simulations
   └─> Apply affect feedback
   └─> Implement fatigue suppression

8. Log System State
   └─> Record clock, state, event counts, simulation counts
```

### Example Episode Output

```python
{
    "clock": 42,
    "state": "awake",
    "num_events": 7,
    "num_simulations": 3
}
```

---

## Technical Specifications

### Performance Characteristics

| Metric | Value |
|--------|-------|
| **Episode Duration** | ~0.001-0.005 seconds |
| **Memory Capacity** | 1000 events (short-term) |
| **Simulation Throughput** | ~100-500 simulations/episode |
| **State Cycle Length** | 500 steps (awake+fatigued+asleep) |

### Memory Requirements

- **Short-term Memory**: ~100 KB (1000 events × ~100 bytes)
- **Simulation History**: Grows linearly with episodes
- **Log Files**: ~1-5 MB per 1000 episodes

### Scalability

- **Tested Range**: 1-10,000 episodes
- **Recommended Max**: 50,000 episodes (for memory constraints)
- **Parallel Processing**: Not currently implemented

---

## Output and Logging

### Log File Structure

Location: `logs/simulation.log`

**Sample Log Entries**:
```
2024-12-12 10:30:15 - INFO - Episode 0 complete
2024-12-12 10:30:16 - INFO - Episode 10 complete
2024-12-12 10:30:17 - INFO - Episode 20 complete
...
2024-12-12 10:31:45 - INFO - Simulation complete.
```

### Internal Data Tracking

The simulation maintains internal logs accessible via:
```python
sim = RPMEESimulation()
sim.run(episodes=100)
print(sim.logs)  # List of episode summaries
```

**Log Entry Schema**:
```python
{
    "clock": 100,
    "state": "awake",
    "num_events": 5,
    "num_simulations": 2
}
```

---

## Development

### Project Structure

```
RPM-EE_Simulation/
│
├── src/
│   ├── main.py           # Entry point
│   ├── simulation.py     # Orchestration class
│   ├── sensory.py        # Sensory input generation
│   ├── salience.py       # Emotional tagging
│   ├── memory.py         # Pattern matching & storage
│   ├── rpm.py            # Recursive predictive modeling
│   ├── emotion.py        # Emotional encoding
│   └── replay.py         # Mode arbitration
│
├── config/
│   └── logging.yaml      # Logging configuration
│
├── logs/                 # Auto-generated log files
│
└── README.md             # This file
```

### Extending the System

#### Adding New Sensory Modalities

Edit `src/sensory.py`:
```python
def _simulate_proprioception(self):
    return [{
        "modality": "proprioception",
        "intensity": random.uniform(0.0, 1.0),
        "duration": 1
    }]
```

#### Customizing Emotional Categories

Modify `src/salience.py` to add emotion types:
```python
emotion_categories = ["joy", "fear", "anger", "sadness", "surprise", "disgust", "awe"]
```

#### Implementing Action Execution

Extend `src/simulation.py`:
```python
def execute_action(self, simulations):
    # Select highest-weight simulation
    best_sim = max(simulations, key=lambda s: s["replay_weight"])
    # Implement action logic here
    pass
```

### Testing Strategies

**Unit Testing Example**:
```python
def test_sensory_state_transition():
    sensory = SensoryInputSystem()
    initial_state = sensory.state
    sensory.state_timer = 0
    sensory.update_clock()
    assert sensory.state != initial_state
```

**Integration Testing**:
```python
def test_full_pipeline():
    sim = RPMEESimulation()
    sim.step()
    assert len(sim.logs) == 1
    assert sim.clock == 1
```

---

## Troubleshooting

### Common Issues

#### 1. No Log Output

**Problem**: `logs/simulation.log` is not created

**Solution**:
```bash
mkdir -p logs
python src/main.py
```

#### 2. Import Errors

**Problem**: `ModuleNotFoundError: No module named 'sensory'`

**Solution**: Run from project root directory:
```bash
cd /path/to/RPM-EE_Simulation
python src/main.py
```

#### 3. Slow Execution

**Problem**: Episodes take too long

**Cause**: Large memory accumulation in long simulations

**Solution**: Add periodic memory pruning:
```python
if episode % 100 == 0:
    sim.memory.prune_old_memory()
```

#### 4. Unexpected State Transitions

**Problem**: States change too frequently

**Solution**: Adjust state durations in `src/sensory.py`:
```python
self.state_durations = {
    "awake": 500,    # Increase from 300
    "fatigued": 150, # Increase from 100
    "asleep": 150    # Increase from 100
}
```

---

## Future Enhancements

### Planned Features

- [ ] **Action Execution Module**: Implement behavioral output based on simulations
- [ ] **Visualization Dashboard**: Real-time plotting of emotional states and memory patterns
- [ ] **External Environment**: Interactive task environments for goal-directed behavior
- [ ] **Neural Network Integration**: Replace rule-based systems with learned models
- [ ] **Multi-Agent Scenarios**: Simulate social interactions and theory of mind
- [ ] **Sleep-Specific Replay**: Implement REM/NREM-like memory consolidation
- [ ] **Adversarial Testing**: Stress-test emotional encoding under extreme conditions

### Research Applications

This simulation can be used to study:
- **Rumination Dynamics**: How emotional feedback loops sustain negative thought patterns
- **Creativity and Innovation**: Role of reward distortion in generating novel ideas
- **PTSD Models**: Pathological replay of high-emotion traumatic events
- **Dream Generation**: Emotional prioritization in offline memory consolidation
- **Decision Biases**: How affective states distort risk assessment

---

## References

### Theoretical Foundations

1. **Predictive Processing**:
   - Clark, A. (2013). *Whatever next? Predictive brains, situated agents, and the future of cognitive science*. Behavioral and Brain Sciences, 36(3), 181-204.

2. **Emotional Memory**:
   - LaBar, K. S., & Cabeza, R. (2006). *Cognitive neuroscience of emotional memory*. Nature Reviews Neuroscience, 7(1), 54-64.

3. **Mental Simulation**:
   - Schacter, D. L., et al. (2012). *The future of memory: Remembering, imagining, and the brain*. Neuron, 76(4), 677-694.

4. **Replay and Consolidation**:
   - Carr, M. F., Jadhav, S. P., & Frank, L. M. (2011). *Hippocampal replay in the awake state: A potential substrate for memory consolidation and retrieval*. Nature Neuroscience, 14(2), 147-153.

### Related Projects

- **ACT-R**: Adaptive Control of Thought-Rational cognitive architecture
- **Soar**: Symbolic cognitive architecture for general intelligence
- **LIDA**: Learning Intelligent Distribution Agent framework

---

## Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the Repository**
2. **Create a Feature Branch**: `git checkout -b feature/your-feature-name`
3. **Make Changes**: Follow existing code style and conventions
4. **Test Thoroughly**: Ensure no regressions
5. **Submit Pull Request**: Include detailed description of changes

### Code Style

- Follow PEP 8 conventions
- Use descriptive variable names
- Add docstrings to new functions/classes
- Keep functions focused and modular

---

## License

This project is provided as-is for research and educational purposes. Please cite appropriately if used in academic work.

---

## Contact

For questions, issues, or collaboration opportunities, please open an issue on the GitHub repository.

**Version**: 1.1.0  
**Last Updated**: December 2024  
**Maintainer**: cleveland-lewis
