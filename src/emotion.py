class EmotionalEncoder:
    def __init__(self):
        # Threshold for how many times a simulation can be replayed before fatigue applies
        self.replay_fatigue_threshold = 3
        # Dictionary to track replay counts for each simulation by ID
        self.simulation_replay_count = {}

    def encode_simulations(self, simulations):
        """
        Apply emotional encoding to each simulation object in the list.

        This function:
        - Tracks replay counts per simulation to apply fatigue after threshold
        - Calculates emotional intensity from the simulation's emotional prediction
        - Calculates affect feedback to bias replay weighting
        - Applies fatigue suppression by reducing replay weight after threshold

        Args:
            simulations (list of dict): List of simulation objects, each expected
                                        to have keys: 'id', 'emotional_prediction',
                                        'replay_weight', 'reward_distortion'

        Returns:
            list of dict: The updated list of simulations with added keys:
                          'emotion_intensity', 'affect_feedback', 'replay_weight' updated,
                          and 'fatigue_flag' boolean.
        """
        for sim in simulations:
            sim_id = sim.get("id")
            if sim_id is None:
                # Skip simulations without an ID to avoid key errors
                continue

            # Initialize replay count if not present
            self.simulation_replay_count.setdefault(sim_id, 0)
            self.simulation_replay_count[sim_id] += 1

            # Calculate emotion intensity safely
            emotional_prediction = sim.get("emotional_prediction", 0.0)
            sim["emotion_intensity"] = abs(emotional_prediction)

            # Calculate affect feedback with safe access to keys
            sim["affect_feedback"] = self._calculate_affect_feedback(sim)

            # Safely update replay weight, initialize if missing
            sim["replay_weight"] = sim.get("replay_weight", 0.0) + sim["affect_feedback"]

            # Apply emotional fatigue suppression after replay threshold
            if self.simulation_replay_count[sim_id] > self.replay_fatigue_threshold:
                sim["replay_weight"] *= 0.5
                sim["fatigue_flag"] = True
            else:
                sim["fatigue_flag"] = False

        return simulations

    @staticmethod
    def _calculate_affect_feedback(sim):
        """
        Calculate affect feedback value based on emotional intensity and reward distortion.

        The affect feedback biases replay weight upwards for highly emotional and distorted
        simulations, gives moderate bias for medium emotion intensity, and suppresses weak emotions.

        Args:
            sim (dict): Simulation object expected to have 'emotion_intensity' and
                        'reward_distortion' keys.

        Returns:
            float: Affect feedback value to add to replay weight.
        """
        reward_distortion = sim.get("reward_distortion", 0.0)
        emotion_intensity = sim.get("emotion_intensity", 0.0)

        # Reinforce high-emotion, high-distortion simulations strongly
        if reward_distortion > 0.4 and emotion_intensity > 0.6:
            return 0.6  # strong positive bias

        # Moderate positive bias for medium emotion intensity
        elif emotion_intensity > 0.5:
            return 0.3

        # Small positive bias for low-medium emotion intensity
        elif emotion_intensity > 0.2:
            return 0.1

        # Negative bias to suppress weak or no emotional effect
        else:
            return -0.1
