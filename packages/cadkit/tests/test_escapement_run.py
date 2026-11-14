"""A recoil escapement run with forces: it ticks, it stalls, friction holds, units are right."""

import math
from itertools import pairwise

import pytest
from cadkit.features.escapement import RecoilEscapement
from cadkit.features.escapement_run import Drive, Pendulum, run

# the clockwork king's escapement, wheel and pendulum
KING = RecoilEscapement(teeth=25, tip_radius=12.7, span=4, release=4.0, drop=0.5, land=0.2)
LENGTH, DEPTH, TURN = 5.5, 3.2, 144.0
# the wheel stands a little short of the pallet that stops it when the anchor is centred
REST = KING.settle(-math.degrees(KING.impulse / KING.tip_radius), 0.0, LENGTH) - 0.4
PENDULUM = Pendulum(inertia=2521.0, mass=7.0, arm=14.0, drag=21.0, stop=8.5)


def _drive(torque: float, loss: float = 0.0, lean: float = 0.0) -> Drive:
    return Drive(
        turn=TURN,
        torque=lambda turned: torque if turned < TURN else 0.0,
        inertia=lambda turned: 170.0 if turned < TURN else 120.0,
        loss=lambda turned: loss,
        lean=lambda turned: lean if turned < TURN else 0.0,
        drag=9.0,
    )


def _run(drive: Drive, pendulum: Pendulum = PENDULUM, **more):
    settings = {"depth": DEPTH, "length": LENGTH, "progress": REST, **more}
    return run(KING, drive, pendulum, **settings)


def test_it_ticks_two_beats_for_every_tooth():
    found = _run(_drive(300.0))
    assert 1.5 < found.finished < 3.0
    assert found.times[-1] < found.finished + 1.5  # the pendulum dies down and the run ends
    driven = [side for time, side in found.beats if time <= found.finished]
    # ten teeth, twenty beats; the one under way as the drive runs down may fall either side
    assert abs(len(driven) - KING.beats(TURN)) <= 1
    assert all(a != b for a, b in pairwise(driven))  # the pallets take turns
    gaps = [b[0] - a[0] for a, b in pairwise(found.beats[2:20])]
    assert max(gaps) < 1.6 * min(gaps)  # and evenly
    low, high = found.swing(0.3, found.finished)
    assert low < -KING.release - 1 and high > KING.release + 1  # it swings past the release
    assert abs(low) <= PENDULUM.stop + 0.1 and high <= PENDULUM.stop + 0.1
    assert found.flank < 0.02  # no nose meets a flank
    assert found.at(0.0) == (0.0, 0.0)
    assert found.at(100.0) == (found.turned[-1], found.angles[-1])
    assert found.at(found.finished)[0] == pytest.approx(TURN, abs=1.0)


def test_too_little_torque_stalls_and_the_run_ends():
    found = _run(_drive(100.0))
    assert found.finished is None
    assert found.times[-1] < 2.0  # long before the limit
    assert 0.0 < found.turned[-1] < KING.pitch  # the first tooth lies on its pallet
    assert abs(found.angles[-1]) < KING.release  # and cannot push it out
    assert len(found.beats) == 1


def test_friction_in_the_train_takes_its_share_both_ways():
    assert _run(_drive(300.0, loss=0.2)).finished > _run(_drive(300.0)).finished
    assert _run(_drive(300.0, loss=0.5)).finished is None
    # a drive that loses everything does not start at all
    still = _run(_drive(300.0, loss=1.0))
    assert still.turned[-1] == 0.0 and still.times[-1] < 0.3


def test_a_frame_that_leans_shifts_the_swing():
    upright = _run(_drive(300.0)).swing(0.3, 1.5)
    leaning = _run(_drive(300.0, lean=-2.0)).swing(0.3, 1.5)
    assert leaning[1] < upright[1] - 0.5  # it swings less far against the lean


def test_a_free_pendulum_has_the_period_of_its_mass_and_arm():
    free = Pendulum(inertia=2521.0, mass=7.0, arm=14.0)
    idle = Drive(turn=TURN, torque=lambda turned: 0.0, inertia=lambda turned: 120.0)
    # the wheel stands in the middle of its drop, so a small swing touches no tooth
    middle = KING.settle(REST, 0.0, LENGTH) - math.degrees(KING.drop / KING.tip_radius) / 2
    found = _run(idle, free, progress=middle, angle=1.0, sample=0.001, limit=1.0)
    crossings = [t for t, (a, b) in zip(found.times[1:], pairwise(found.angles)) if a > 0 >= b]
    period = 2 * math.pi * math.sqrt(2521.0 / (7.0 * 9810.0 * 14.0))  # g mm2 over g mm2/s2
    assert period == pytest.approx(0.3218, abs=1e-3)
    assert crossings[1] - crossings[0] == pytest.approx(period, rel=0.01)
    assert max(found.angles[600:]) == pytest.approx(1.0, abs=0.02)  # and loses nothing
    assert found.turned[-1] == 0.0


def test_dry_friction_holds_a_pendulum_that_gravity_cannot_move():
    idle = Drive(turn=TURN, torque=lambda turned: 0.0, inertia=lambda turned: 120.0)
    middle = KING.settle(REST, 0.0, LENGTH) - math.degrees(KING.drop / KING.tip_radius) / 2
    # one degree off plumb gravity turns it with 16.8 mN mm; the arbor holds 21
    held = _run(idle, PENDULUM, progress=middle, angle=1.0)
    assert held.angles[-1] == 1.0 and held.times[-1] == pytest.approx(0.25, abs=0.02)
    slipping = _run(idle, PENDULUM, progress=middle, angle=2.0)
    assert slipping.angles[-1] < 1.5


def test_landing_with_speed_kicks_the_anchor():
    slow = _run(_drive(300.0))
    kicked = _run(_drive(300.0), speed=1500.0)
    assert kicked.beats[0][0] < 0.002  # the wheel is on its pallet at once
    assert kicked.angles[3] < slow.angles[3] - 1.0  # after 0.03 s


def test_bad_inputs_are_refused():
    with pytest.raises(ValueError, match="step"):
        _run(_drive(300.0), step=0.02, sample=0.01)
    with pytest.raises(ValueError, match="depth"):
        _run(_drive(300.0), depth=0.0)
    with pytest.raises(ValueError, match="Inertia"):
        _run(Drive(turn=TURN, torque=lambda turned: 300.0, inertia=lambda turned: 0.0))
    # without a stop an anchor thrown far over reaches the wheel's root
    loose = Pendulum(inertia=2521.0, mass=7.0, arm=14.0, drag=21.0)
    with pytest.raises(ValueError, match="root"):
        _run(_drive(300.0), loose, angle=20.0)
