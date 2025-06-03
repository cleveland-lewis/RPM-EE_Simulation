import logging
from transitions import Machine, MachineError
import time

class ReplayController:
    """
    Finite State Machine for replay mode control in RPM-EE.
    Transitions are driven by system state conditions such as
    prediction error, schema stress, and emotional volatility.
    """

    states = ["explore", "converge", "stabilize"]

    def __init__(self, cooldown=0.1):
        self.machine = Machine(model=self, states=ReplayController.states, initial="explore")
        self.machine.add_transition("gain_clarity", "explore", "converge", after="log_transition")
        self.machine.add_transition("destabilize", ["converge", "stabilize"], "explore", after="log_transition")
        self.machine.add_transition("settle", "converge", "stabilize", after="log_transition")

        # Set up logging (only once per process)
        self.transition_log = []
        if not logging.getLogger().handlers:
            logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Cooldown to prevent rapid flip-flop
        self.last_transition_time = 0
        self.cooldown = cooldown

    def log_transition(self):
        entry = f"Transitioned to {self.state}"
        self.transition_log.append(entry)
        self.logger.info(entry)

    def update_state(self, system_state: dict):
        """
        Update state based on RPM-EE system metrics.

        Args:
            system_state (dict): contains keys like prediction_error, stress, emotion_volatility

        Returns:
            str: new replay mode state
        """
        now = time.time()
        if now - self.last_transition_time < self.cooldown:
            return self.state

        pe = system_state.get("prediction_error", 0.0)
        stress = system_state.get("stress", 0.0)
        volatility = system_state.get("emotion_volatility", 0.0)

        try:
            if self.state == "explore" and pe < 0.3 and volatility < 0.4:
                self.gain_clarity()
                self.last_transition_time = time.time()
            elif self.state == "converge":
                if volatility > 0.6 or pe > 0.5:
                    self.destabilize()
                    self.last_transition_time = time.time()
                elif stress < 0.2:
                    self.settle()
                    self.last_transition_time = time.time()
            elif self.state == "stabilize" and pe > 0.4:
                self.destabilize()
                self.last_transition_time = time.time()
        except MachineError as e:
            self.logger.warning(f"Tried illegal transition from {self.state}: {e}")

        return self.state
