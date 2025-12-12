# RPM-EE Salience Tagger (v1.1.0)

import uuid
import random
from datetime import datetime

class SalienceTagger:
    """
    Converts raw sensory inputs into tagged events with:
    - Unique IDs
    - Emotion (valence, category)
    - Novelty score
    - Prioritization score
    - Timing information
    """
    
    # Constants
    INTENSITY_NOVELTY_SCALE = 2.0  # Scaling factor for intensity differences to novelty
    
    def __init__(self):
        self.emotion_categories = ["awe", "joy", "fear", "disgust", "anger", "sadness", "surprise", "neutral"]
        self.event_history = []
        
    def tag_input(self, input_packet):
        """
        Convert raw sensory input packet to list of tagged events.
        
        Args:
            input_packet: Dict with keys: clock, state, vision, hearing, touch, smell, taste
                         Each sensory modality is a list of raw sensory dicts
        
        Returns:
            List of tagged event dicts with full schema
        """
        tagged_events = []
        clock = input_packet.get("clock", 0)
        state = input_packet.get("state", "awake")
        
        # Process each sensory modality
        for modality in ["vision", "hearing", "touch", "smell", "taste"]:
            raw_inputs = input_packet.get(modality, [])
            for raw_input in raw_inputs:
                event = self._create_event(raw_input, clock, state)
                tagged_events.append(event)
                self.event_history.append(event)
        
        return tagged_events
    
    def _create_event(self, raw_input, clock, state):
        """Create a fully tagged event from raw sensory input."""
        # Extract raw properties
        modality = raw_input.get("modality", "unknown")
        intensity = raw_input.get("intensity", 0.5)
        duration = raw_input.get("duration", 1)
        
        # Generate emotion
        emotion = self._generate_emotion(modality, intensity, state)
        
        # Calculate novelty
        novelty = self._calculate_novelty(modality, intensity)
        
        # Calculate timing (normalized to 0-1 based on state cycle)
        timing = self._calculate_timing(clock, state)
        
        # Calculate prioritization score (0-10 scale)
        prioritization_score = self._calculate_prioritization(intensity, novelty, emotion, state)
        
        # Create event
        event = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "modality": modality,
            "state": state,
            "novelty": round(novelty, 3),
            "emotion": emotion,
            "recurrence": 0,  # Will be updated by memory system
            "timing": round(timing, 3),
            "duration": duration,
            "intensity": round(intensity, 3),
            "prioritization_score": round(prioritization_score, 2)
        }
        
        return event
    
    def _generate_emotion(self, modality, intensity, state):
        """Generate emotion with valence and category based on input characteristics."""
        # Base valence on intensity and modality
        if state == "asleep":
            # Dreams: more extreme emotions
            valence = random.uniform(-1.0, 1.0)
        else:
            # Awake/fatigued: intensity-based with noise
            valence = (intensity - 0.5) * 2  # Map 0-1 to -1 to 1
            valence += random.gauss(0, 0.2)  # Add noise
            valence = max(-1.0, min(1.0, valence))  # Clamp
        
        # Select category based on valence and modality
        if valence > 0.6:
            category = random.choice(["joy", "awe", "surprise"])
        elif valence < -0.6:
            category = random.choice(["fear", "disgust", "anger", "sadness"])
        elif valence < -0.2:
            category = random.choice(["sadness", "fear"])
        elif valence > 0.2:
            category = random.choice(["joy", "surprise"])
        else:
            category = "neutral"
        
        return {
            "valence": round(valence, 3),
            "category": category
        }
    
    def _calculate_novelty(self, modality, intensity):
        """Calculate how novel this event is compared to recent history."""
        if not self.event_history:
            return 1.0  # First event is maximally novel
        
        # Simple novelty: compare to recent events of same modality
        recent_same_modality = [
            e for e in self.event_history[-20:] 
            if e.get("modality") == modality
        ]
        
        if not recent_same_modality:
            return 0.8  # New modality is quite novel
        
        # Compare intensity
        avg_intensity = sum(e.get("intensity", 0) for e in recent_same_modality) / len(recent_same_modality)
        intensity_diff = abs(intensity - avg_intensity)
        
        novelty = min(1.0, intensity_diff * self.INTENSITY_NOVELTY_SCALE)
        return novelty
    
    def _calculate_timing(self, clock, state):
        """Calculate timing as normalized position in state cycle."""
        # Timing represents where in the current state cycle we are (0-1)
        state_durations = {"awake": 300, "fatigued": 100, "asleep": 100}
        total_cycle = sum(state_durations.values())
        
        # Simplified: use clock modulo cycle length
        position_in_cycle = clock % total_cycle
        timing = position_in_cycle / total_cycle
        
        return timing
    
    def _calculate_prioritization(self, intensity, novelty, emotion, state):
        """Calculate prioritization score (0-10) for event importance."""
        # Higher priority for:
        # - High intensity
        # - High novelty
        # - Extreme emotions (positive or negative)
        # - Events while awake (vs asleep)
        
        score = 0.0
        
        # Intensity contribution (0-3)
        score += intensity * 3
        
        # Novelty contribution (0-2)
        score += novelty * 2
        
        # Emotion contribution (0-3)
        emotion_intensity = abs(emotion.get("valence", 0))
        score += emotion_intensity * 3
        
        # State contribution (0-2)
        if state == "awake":
            score += 2
        elif state == "fatigued":
            score += 1
        # asleep gets 0
        
        return min(10.0, score)  # Cap at 10