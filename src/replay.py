from .replay_fsm import ReplayController

class ReplayModeArbitrator:
    def __init__(self):
        self.controller = ReplayController()

    def select_mode(self, system_state):
        return self.controller.update_state(system_state)
