"""
SimulationClock.

Responsibilities:
- Maintain current simulation index
- Control time flow (pause/resume)
- Provide simulation speed (1:N)
- Indicate session completion

Clock operates on index, not real time.
"""

from core.settings import SIMULATION_SPEED


class SimulationClock:
    def __init__(self, max_index: int, speed: int = SIMULATION_SPEED):
        if max_index <= 0:
            raise ValueError("max_index must be > 0")

        self._current_index: int = 0
        self._max_index: int = max_index
        self._is_paused: bool = False
        self._speed: int = speed

    # --- state access ---

    @property
    def current_index(self) -> int:
        return self._current_index

    @property
    def speed(self) -> int:
        return self._speed

    @property
    def is_paused(self) -> bool:
        return self._is_paused

    # --- core logic ---

    def tick(self) -> bool:
        """
        Move simulation forward by one step.

        Returns:
            bool: True if advanced, False if paused or finished
        """

        if self._is_paused:
            return False

        if self.is_finished():
            return False

        self._current_index += 1
        return True

    def pause(self) -> None:
        self._is_paused = True

    def resume(self) -> None:
        self._is_paused = False

    def reset(self) -> None:
        self._current_index = 0
        self._is_paused = False

    def is_finished(self) -> bool:
        return self._current_index >= self._max_index - 1

    # --- helpers ---

    def progress(self) -> float:
        """
        Returns progress from 0.0 to 1.0
        """
        return self._current_index / (self._max_index - 1)

    def remaining_steps(self) -> int:
        return max(0, (self._max_index - 1) - self._current_index)