class ReplayModeArbitrator:
    def __init__(self, damping_cycles=5):
        self.damping_cycles = damping_cycles
        self.current_mode = 'rest'
        self.last_switch_clock = -damping_cycles  # Initialize so switching allowed immediately

    def select_mode(self, system_state):
        clock = system_state.get('clock', 0)
        stress = system_state.get('stress', 0.0)
        prediction_error = system_state.get('prediction_error', 0.0)
        emotion_volatility = system_state.get('emotion_volatility', 0.0)

        stress_threshold = 0.7
        error_threshold = 0.6
        volatility_threshold = 0.5

        # Prevent switching if within damping period
        if clock - self.last_switch_clock < self.damping_cycles:
            return self.current_mode

        # Determine new mode based on priority order
        if stress > stress_threshold:
            new_mode = 'soothing'
        elif prediction_error > error_threshold:
            new_mode = 'problem_solving'
        elif emotion_volatility > volatility_threshold:
            new_mode = 'pattern_search'
        else:
            new_mode = 'rest'

        # Update if mode changed
        if new_mode != self.current_mode:
            self.current_mode = new_mode
            self.last_switch_clock = clock

        return self.current_mode