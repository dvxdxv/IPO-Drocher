from domain.clock import SimulationClock


def test_clock_tick():
    clock = SimulationClock(max_index=10)

    clock.tick()
    assert clock.current_index == 1


def test_clock_pause():
    clock = SimulationClock(max_index=10)

    clock.pause()
    clock.tick()

    assert clock.current_index == 0


def test_clock_resume():
    clock = SimulationClock(max_index=10)

    clock.pause()
    clock.resume()
    clock.tick()

    assert clock.current_index == 1


def test_clock_end():
    clock = SimulationClock(max_index=2)

    clock.tick()
    clock.tick()

    assert clock.is_finished()