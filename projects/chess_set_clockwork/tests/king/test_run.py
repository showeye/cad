"""Whether the king ticks: masses from the solids, friction in the guide, a move run through."""

import pytest
from cadkit.features.escapement_run import GRAVITY
from chess_set_clockwork.king._layout import layout
from chess_set_clockwork.king._run import at_escape, carried, drive, landing
from chess_set_clockwork.king.model import Params, balance, ticking, weights

P = Params()
L = layout(P)
M = weights(P)
WEIGHT = M.body * GRAVITY * 1e-3  # mN on the pawl if nothing rubbed
FALL = P.travel - L.stroke  # the furthest the king can drop onto its pawl


def test_masses_come_from_the_solids():
    found = balance(P)
    assert M.body == pytest.approx(found["drive"])
    assert M.pendulum[0] == pytest.approx(found["pendulum"])
    assert M.centre == pytest.approx((0.0, 0.27), abs=0.05)  # the bob pulls it to the back
    assert M.pendulum[1] == pytest.approx(2521, abs=20)  # g mm2 about the anchor's arbor
    assert M.arm == pytest.approx(14.0, abs=0.1) and M.hang == pytest.approx(0.085, abs=0.02)
    assert M.great == pytest.approx((2.01, 98.5), abs=0.5)
    assert M.escape == pytest.approx((2.38, 105.5), abs=0.5)


def test_the_king_leans_on_its_guide_and_rubs():
    turns = range(-60, 1, 10)
    for turn in turns:  # without friction the pawl carries the whole body
        assert carried(P, M, turn, 0.0)[0] == pytest.approx(WEIGHT)
    shares = [carried(P, M, turn, 0.3)[0] / WEIGHT for turn in turns]
    assert shares[0] == pytest.approx(0.56, abs=0.01) and shares[-1] == pytest.approx(
        0.60, abs=0.01
    )
    assert shares == sorted(shares)  # the guide grows longer as the plunger goes home
    assert carried(P, M, -60, 0.2)[0] / WEIGHT == pytest.approx(0.68, abs=0.01)
    # it leans to the left and to the back by the guide's play over the guide's length
    assert carried(P, M, -60, 0.3)[1:] == pytest.approx((2.10, 3.06), abs=0.02)
    assert carried(P, M, 0, 0.3)[1:] == pytest.approx((1.74, 2.53), abs=0.02)


def test_friction_leaves_two_fifths_of_the_torque():
    low, high = balance(P)["torque"]  # mN m on the star
    ideal = [at_escape(P, M, -60 + 2.5 * i, 0.0, 0.0) for i in range(25)]
    assert all(real == pytest.approx(full) for full, real in ideal)
    assert min(full for full, _ in ideal) == pytest.approx(low * 1000 / L.ratio)
    assert max(full for full, _ in ideal) == pytest.approx(high * 1000 / L.ratio)
    # mN mm at the escape wheel with a friction of 0.3 everywhere, and of 0.2
    assert at_escape(P, M, -60, 0.3, 0.3) == pytest.approx((318, 113), abs=2)
    assert at_escape(P, M, 0, 0.3, 0.3) == pytest.approx((431, 183), abs=2)
    assert at_escape(P, M, -60, 0.2, 0.2)[1] == pytest.approx(161, abs=2)
    assert at_escape(P, M, -60, 0.3, 0.0)[1] > at_escape(P, M, -60, 0.3, 0.3)[1] + 25  # the pins


def test_drive_ends_when_the_king_stands_on_the_board():
    weight = drive(P, M, 0.2, 0.2)
    assert weight.turn == pytest.approx(144)
    assert weight.torque(0.0) == pytest.approx(318, abs=1)
    assert weight.torque(143.9) > 400 and weight.torque(144.0) == 0.0 == weight.loss(144.0)
    wheels = M.escape[1] + M.great[1] / L.ratio**2
    assert weight.inertia(144.0) == pytest.approx(wheels)
    assert weight.inertia(0.0) == pytest.approx(wheels + M.body * (L.ratchet.arm(-60) / 2.4) ** 2)
    # sinking, the king leans and the pendulum hangs off the anchor's centre
    assert weight.lean(0.0) == pytest.approx(M.hang - 2.10, abs=0.02)
    assert weight.lean(150.0) == M.hang
    assert weight.drag == pytest.approx(6.3, abs=0.1)  # mN mm: the wheels' own weight


def test_landing_on_the_pawl_starts_the_wheel():
    assert FALL == pytest.approx(0.856, abs=0.002)
    assert landing(P, M, 0.0) == 0.0
    assert landing(P, M, FALL) == pytest.approx(1559, abs=20)  # degrees a second
    with pytest.raises(ValueError, match="fall"):
        landing(P, M, FALL + 0.5)


@pytest.mark.parametrize(
    "conditions",
    [
        {"friction": 0.2, "pin_friction": 0.2},
        {"friction": 0.2, "pin_friction": 0.2, "fall": FALL},
        {"friction": 0.25, "pin_friction": 0.25},
        {"friction": 0.27, "pin_friction": 0.27, "fall": FALL},
        {"friction": 0.3, "pin_friction": 0.1},
    ],
)
def test_the_king_ticks_through_a_move_with_a_friction_up_to_a_quarter(conditions):
    ran = ticking(P, **conditions)
    assert 1.9 < ran.finished < 2.4  # seconds for one move
    assert ran.finished + 0.4 < ran.times[-1] < ran.finished + 1.3  # the pendulum dies down
    driven = [side for time, side in ran.beats if time <= ran.finished]
    assert abs(len(driven) - 20) <= 1
    low, high = ran.swing(0.3, ran.finished)
    # the king leans two degrees while it sinks, so the anchor swings further to one side
    assert -P.swing_stop - 0.1 < low < -6.5 and P.release + 0.8 < high < 6.0
    assert ran.flank < 0.02  # no nose of a pallet meets the flank of a tooth
    # on the board the wheels are free and may run on until a pallet stops them
    assert 143.5 < ran.turned[-1] < 144 + L.escapement.pitch / 2 + 1


@pytest.mark.parametrize(("friction", "fall"), [(0.26, 0.0), (0.28, FALL), (0.3, 0.0), (0.3, FALL)])
def test_the_king_as_built_stalls_with_a_friction_of_three_tenths(friction, fall):
    """The open point of this build: see docs/king-design-notes.md, section 11.

    Lowered onto its pawl it ticks up to 0.25, dropped onto it up to 0.27.
    """
    ran = ticking(P, friction=friction, pin_friction=friction, fall=fall)
    assert ran.finished is None and ran.times[-1] < 1.0
    # the second tooth lies on its pallet and cannot push it out against the king's lean
    assert len(ran.beats) == 2 and ran.turned[-1] < L.escapement.pitch
    assert 0 < ran.angles[-1] < P.release + 0.5
    # with four tenths the first tooth does not get its pallet out either, unless it is dropped
    assert len(ticking(P, friction=0.4, pin_friction=0.4).beats) == 1


def test_a_pendulum_left_swinging_helps_the_start_but_not_the_run():
    """Start-up is the weak point: a swinging pendulum can carry a start that fails from rest."""
    assert ticking(P, friction=0.3, pin_friction=0.3, angle=-8.0).finished < 2.5
    assert ticking(P, friction=0.3, pin_friction=0.3, angle=-4.0).finished is None
    # a little more friction and the king stops within a few beats wherever the pendulum was
    for angle in (-8.0, -4.0, 0.0, 4.0, 8.0):
        ran = ticking(P, friction=0.33, pin_friction=0.33, angle=angle)
        assert ran.finished is None and len(ran.beats) <= 8
