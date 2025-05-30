from .replay_fsm import ReplayController

class ReplayModeArbitrator:
    def __init__(self, damping_cycles=5):
        self.controller = ReplayController()
        self.damping_cycles = damping_cycles
        self.current_mode = 'rest'  # or default mode
        self.last_switch_clock = 0

    def select_mode(self, system_state):
        return self.controller.update_state(system_state)
