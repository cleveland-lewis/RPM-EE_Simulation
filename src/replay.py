class ReplayModeArbitrator:
    def __init__(self, damping_cycles=5):
        self.current_mode = "problem_solving"
        self.last_switch_clock = 0
        self.damping_cycles = damping_cycles

    def select_mode(self, system_state):
        clock = system_state["clock"]
        stress = system_state["stress"]
        prediction_error = system_state["prediction_error"]
        emotion_volatility = system_state["emotion_volatility"]

        if (clock - self.last_switch_clock) < self.damping_cycles:
            return self.current_mode  # Enforce mode duration

        if stress > 0.7:
            self._switch_mode("soothing", clock)
        elif prediction_error > 0.6:
            self._switch_mode("problem_solving", clock)
        elif emotion_volatility > 0.5:
            self._switch_mode("pattern_search", clock)
        else:
            self._switch_mode("rest", clock)

        return self.current_mode

    def _switch_mode(self, new_mode, clock):
        if new_mode != self.current_mode:
            self.current_mode = new_mode
            self.last_switch_clock = clock
