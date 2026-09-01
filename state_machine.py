import random
from PyQt6.QtCore import QTimer, QObject, pyqtSignal

class VitalsSystem(QObject):
    vitals_updated = pyqtSignal(dict)

    def __init__(self, hunger: float = 100.0, energy: float = 100.0, happiness: float = 100.0):
        super().__init__()
        self.hunger = hunger       # 100 = full, 0 = starving
        self.energy = energy       # 100 = fully rested, 0 = exhausted
        self.happiness = happiness # 100 = ecstatic, 0 = sad

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(2000) # Decay every 2 seconds

    def tick(self):
        # Gradual degradation
        self.hunger = max(0.0, self.hunger - 0.5)
        self.happiness = max(0.0, self.happiness - 0.3)
        self.energy = max(0.0, self.energy - 0.2)

        self.vitals_updated.emit(self.get_status())

    def feed(self):
        self.hunger = min(100.0, self.hunger + 30.0)
        self.happiness = min(100.0, self.happiness + 10.0)
        self.vitals_updated.emit(self.get_status())

    def play(self):
        self.happiness = min(100.0, self.happiness + 20.0)
        self.energy = max(0.0, self.energy - 10.0)
        self.vitals_updated.emit(self.get_status())

    def rest(self):
        self.energy = min(100.0, self.energy + 25.0)
        self.vitals_updated.emit(self.get_status())

    def get_status(self) -> dict:
        return {
            "hunger": round(self.hunger, 1),
            "energy": round(self.energy, 1),
            "happiness": round(self.happiness, 1),
        }


class PetBehaviorEngine(QObject):
    state_changed = pyqtSignal(str)

    def __init__(self, min_seconds: int = 3, max_seconds: int = 8):
        super().__init__()
        self.min_ms = min_seconds * 1000
        self.max_ms = max_seconds * 1000
        self.states = ["idle", "walk_left", "walk_right"]
        self.current_state = "idle"
        self.vitals = VitalsSystem()

        self.vitals.vitals_updated.connect(self._check_vitals_thresholds)

        self.behavior_timer = QTimer(self)
        self.behavior_timer.timeout.connect(self.decide_next_state)
        self.behavior_timer.start(random.randint(self.min_ms, self.max_ms))

    def set_state(self, new_state: str):
        if new_state in ["idle", "walk_left", "walk_right", "sleep"]:
            self.current_state = new_state
            self.state_changed.emit(self.current_state)

    def decide_next_state(self):
        # If sleeping, restore energy until threshold
        if self.current_state == "sleep":
            self.vitals.rest()
            if self.vitals.energy >= 90.0:
                self.set_state("idle")
            self.behavior_timer.setInterval(random.randint(self.min_ms, self.max_ms))
            return

        # If exhausted, transition to sleep
        if self.vitals.energy <= 15.0:
            self.set_state("sleep")
            self.behavior_timer.setInterval(random.randint(self.min_ms, self.max_ms))
            return

        # Random transition
        self.current_state = random.choice(self.states)
        self.behavior_timer.setInterval(random.randint(self.min_ms, self.max_ms))
        self.state_changed.emit(self.current_state)

    def _check_vitals_thresholds(self, status: dict):
        if status["energy"] <= 10.0 and self.current_state != "sleep":
            self.set_state("sleep")
