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
MARGIN = 0.4  # the friction with which the king has to tick from any start


def test_masses_come_from_the_solids():
    found = balance(P)
    assert M.body == pytest.approx(found["drive"])
    assert M.pendulum[0] == pytest.approx(found["pendulum"])
    assert M.centre == pytest.approx((0.0, 0.0), abs=0.05)
    # a light pendulum on a thin arbor: 4.5 g, of which the steel bob is 1.0 g
    assert M.pendulum == pytest.approx((4.50, 1100), abs=15)  # g, and g mm2 about the arbor
    assert M.arm == pytest.approx(9.63, abs=0.1)
    # the arch is cut so that the pendulum hangs with the anchor where the layout takes it
    assert M.hang == pytest.approx(P.beat, abs=0.05)
    assert M.great == pytest.approx((2.01, 98.5), abs=0.5)
    assert M.escape == pytest.approx((2.28, 94.5), abs=0.5)


def test_the_king_leans_on_its_guide_and_rubs():
    turns = range(-60, 1, 10)
    for turn in turns:  # without friction the pawl carries the whole body
        assert carried(P, M, turn, 0.0)[0] == pytest.approx(WEIGHT)
    shares = [carried(P, M, turn, 0.3)[0] / WEIGHT for turn in turns]
    assert shares[0] == pytest.approx(0.57, abs=0.01) and shares[-1] == pytest.approx(
        0.61, abs=0.01
    )
    assert shares == sorted(shares)  # the guide grows longer as the plunger goes home
    assert carried(P, M, -60, 0.2)[0] / WEIGHT == pytest.approx(0.68, abs=0.01)
    assert carried(P, M, -60, MARGIN)[0] / WEIGHT == pytest.approx(0.48, abs=0.01)
    # it leans to the left and to the back by the guide's play over the guide's length
    assert carried(P, M, -60, 0.3)[1:] == pytest.approx((2.10, 3.06), abs=0.02)
    assert carried(P, M, 0, 0.3)[1:] == pytest.approx((1.74, 2.53), abs=0.02)


def test_friction_leaves_a_quarter_of_the_torque_at_four_tenths():
    low, high = balance(P)["torque"]  # mN m on the star
    ideal = [at_escape(P, M, -60 + 2.5 * i, 0.0, 0.0) for i in range(25)]
    assert all(real == pytest.approx(full) for full, real in ideal)
    assert min(full for full, _ in ideal) == pytest.approx(low * 1000 / L.ratio)
    assert max(full for full, _ in ideal) == pytest.approx(high * 1000 / L.ratio)
    # mN mm at the escape wheel with the same friction everywhere
    assert at_escape(P, M, -60, 0.2, 0.2)[1] == pytest.approx(150, abs=2)
    assert at_escape(P, M, -60, 0.3, 0.3) == pytest.approx((293, 106), abs=2)
    assert at_escape(P, M, 0, 0.3, 0.3) == pytest.approx((397, 170.5), abs=2)
    assert at_escape(P, M, -60, MARGIN, MARGIN)[1] == pytest.approx(74, abs=2)
    assert at_escape(P, M, 0, MARGIN, MARGIN)[1] == pytest.approx(128, abs=2)
    assert at_escape(P, M, -60, 0.3, 0.0)[1] > at_escape(P, M, -60, 0.3, 0.3)[1] + 25  # the pins


def test_drive_ends_when_the_king_stands_on_the_board():
    weight = drive(P, M, 0.2, 0.2)
    assert weight.turn == pytest.approx(144)
    assert weight.torque(0.0) == pytest.approx(293, abs=1)
    assert weight.torque(143.9) > 380 and weight.torque(144.0) == 0.0 == weight.loss(144.0)
    wheels = M.escape[1] + M.great[1] / L.ratio**2
    assert weight.inertia(144.0) == pytest.approx(wheels)
    assert weight.inertia(0.0) == pytest.approx(wheels + M.body * (L.ratchet.arm(-60) / 2.4) ** 2)
    # sinking, the king leans: the pendulum hangs one degree off the anchor's centre instead
    # of two, because standing it hangs one degree off to the other side
    assert weight.lean(0.0) == pytest.approx(M.hang - 2.10, abs=0.02)
    assert weight.lean(0.0) == pytest.approx(-1.1, abs=0.1)
    assert weight.lean(150.0) == M.hang
    assert weight.drag == pytest.approx(6.1, abs=0.1)  # mN mm: the wheels' own weight


def test_landing_on_the_pawl_starts_the_wheel():
    assert FALL == pytest.approx(0.856, abs=0.002)
    assert landing(P, M, 0.0) == 0.0
    assert landing(P, M, FALL) == pytest.approx(1576, abs=20)  # degrees a second
    with pytest.raises(ValueError, match="fall"):
        landing(P, M, FALL + 0.5)


@pytest.mark.parametrize(
    "conditions",
    [
        {"friction": 0.1, "pin_friction": 0.1},
        {"friction": 0.2, "pin_friction": 0.2},
        {"friction": 0.2, "pin_friction": 0.2, "fall": FALL},
        {"friction": 0.3, "pin_friction": 0.3},
        {"friction": MARGIN, "pin_friction": MARGIN},
        {"friction": MARGIN, "pin_friction": MARGIN, "fall": FALL},
        {"friction": 0.5, "pin_friction": 0.5},
    ],
)
def test_the_king_ticks_through_a_move(conditions):
    ran = ticking(P, **conditions)
    assert 0.8 < ran.finished < 1.6  # seconds for one move: slower with more friction
    assert ran.finished + 0.3 < ran.times[-1] < ran.finished + 1.2  # the pendulum dies down
    driven = [side for time, side in ran.beats if time <= ran.finished]
    assert abs(len(driven) - 16) <= 1
    low, high = ran.swing(0.2, ran.finished)
    # the king leans two degrees while it sinks, so the anchor swings further to one side
    assert -P.swing_stop - 0.2 < low < -4.2 and P.release + 0.4 < high < 5.2
    assert ran.flank < 0.02  # no nose of a pallet meets the flank of a tooth
    # on the board the wheels are free and may run on until a pallet stops them
    assert 143.5 < ran.turned[-1] < 144 + L.escapement.pitch / 2 + 1


def test_a_move_takes_longer_with_more_friction():
    times = [ticking(P, friction=mu, pin_friction=mu).finished for mu in (0.1, 0.2, 0.3, MARGIN)]
    assert times == sorted(times)
    assert times[0] == pytest.approx(0.82, abs=0.05) and times[-1] == pytest.approx(1.10, abs=0.05)


@pytest.mark.parametrize("angle", [-7.0, -3.5, 0.0, 3.5, 7.0])
@pytest.mark.parametrize("fall", [0.0, FALL])
@pytest.mark.parametrize("friction", [0.2, MARGIN, 0.45])
def test_the_king_ticks_from_any_start(angle, fall, friction):
    """Wherever the hand has left the pendulum, lowered onto the pawl or dropped onto it."""
    ran = ticking(P, friction=friction, pin_friction=friction, fall=fall, angle=angle)
    assert ran.finished is not None and ran.finished < 1.6
    assert len([side for time, side in ran.beats if time <= ran.finished]) >= 15


@pytest.mark.parametrize(
    "values",
    [
        {"guide": 0.5},  # a loose guide: the king leans 3.1 degrees instead of 2.1
        {"guide": 0.15, "slide": 0.15},  # a tight one: 1.1 degrees
        {"release": 3.5},  # pallets that stand 0.07 mm deeper in the wheel than drawn
    ],
)
def test_the_king_ticks_with_fits_that_print_differently(values):
    other = Params(**values)
    for fall in (0.0, FALL):
        ran = ticking(other, friction=MARGIN, pin_friction=MARGIN, fall=fall)
        assert ran.finished is not None and ran.finished < 1.6


@pytest.mark.parametrize(("friction", "fall"), [(0.52, 0.0), (0.55, 0.0), (0.61, FALL)])
def test_the_king_stalls_with_a_friction_above_a_half(friction, fall):
    """Lowered onto its pawl the king ticks up to 0.51, dropped onto it up to 0.60."""
    ran = ticking(P, friction=friction, pin_friction=friction, fall=fall)
    assert ran.finished is None and ran.times[-1] < 1.0
    # within the first teeth one lies on its pallet and cannot push it out
    assert len(ran.beats) <= 4 and ran.turned[-1] < 2 * L.escapement.pitch
    assert abs(ran.angles[-1]) < P.release + 0.5
    # with six tenths the first tooth does not get its pallet out either, unless it is dropped
    assert len(ticking(P, friction=0.6, pin_friction=0.6).beats) == 1


def test_a_drop_onto_the_pawl_helps_the_start():
    assert ticking(P, friction=0.55, pin_friction=0.55, fall=FALL).finished < 1.6
    assert ticking(P, friction=0.55, pin_friction=0.55).finished is None
