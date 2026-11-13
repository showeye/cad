"""Nikisz massing: the space each house may fill, on its ground block.

These are stand-ins for the decorated houses of the full design, drawn as the largest plain
volumes that the motion proof shows to be free of collision: tall bays (A) stand proud with
wings that lap in front of the low bays (B), so the joint between two houses is never a gap.
The ground block under each house is real: it carries the pavement, laps under its
neighbour, and holds the unit along the street on the blade that passes through it. The
blocks of the two end houses run on into the bookends, so the street has no open end.
"""

from fala._layout import layout
from fala._parts import box, prism_x


def slot_half_width(p) -> float:
    """Half width of the guide slot through block and house: the blade plus the unit's swing.

    The unit leans about its pivot, so the slot's walls swing along the street: most at the
    block's underside for the blade's full width, and at the blade's top for its narrow tip.
    """
    L = layout(p)
    slope = L.cam.eccentricity * L.cam.k
    foot = p.blade_width / 2 + (L.pivot_z - L.block_z) * slope
    tip = min(p.blade_tip, p.blade_width) / 2 + (L.blade_z - L.pivot_z) * slope
    return max(foot, tip) + 0.5


def slot_top(p) -> float:
    """Ceiling of the guide slot inside a house: over the tongue, and over the fixed blade when
    the house is at the bottom of its travel."""
    L = layout(p)
    return max(L.blade_z + p.amplitude, L.tongue_z) + 1.5


KINDS = ("A", "B")

# Tall bay: (half width, front, back, top) of each volume above the pavement.
A_BODY = (8.0, -1.2, 32.0, 36.0)
A_WINGS = (12.3, -3.3, -1.2, 36.0)  # facade plate with plinth and pilasters
A_COPING = (12.3, -3.9, -1.2, 37.8)  # from the eaves up; no wider than the wings
A_ROOF = (8.0, -1.2, 33.0, 39.2)
A_CHIMNEY = (1.2, 5.8, 17.7, 22.3, 43.5)  # x0, x1, y0, y1, top
A_EAVES = 36.0

# Low bay.
B_BODY = (8.5, 1.6, 32.0, 27.0)
B_FACADE = (11.6, -0.6, 1.6, 27.0)  # facade plate with string course
B_ROOF = (10.2, -0.4, 33.0)  # half width, front, back
B_RIDGE = (13.0, 17.0, 34.5)  # y0, y1, top
B_CHIMNEY = (-2.3, 2.3, 12.7, 17.3, 38.5)
B_EAVES = 27.0

JOG_Y = 9.0  # where the joint between two blocks steps sideways, behind the facades
WING_LIFT = 0.5  # a facade that reaches over the neighbour's pavement starts this far above it
OWN = 9.4  # half width of the pavement that belongs to a house alone


def pavement_edges(p) -> tuple[float, float]:
    """X of the left and the right edge of a house's own pavement, about its centre.

    The joint lies half a lap to the right of the line midway between two houses.
    """
    right = p.pitch / 2 - p.joint / 2 + p.lap / 2
    return right + p.joint - p.pitch, right


def front_edges(which: str) -> dict:
    """The upright edges of a house of kind `which` that a viewer in front sees beside the
    joint: {name: (half width, foot, top)} above the pavement.

    A tall bay has one, its wing with the coping, which stands in front of the neighbour. A
    low bay has two, behind the neighbour's wing: its facade plate and the verge of its roof.
    """
    if which[0] == "A":
        return {"wing": (A_WINGS[0], WING_LIFT, A_COPING[3])}
    return {
        "facade": (B_FACADE[0], WING_LIFT, B_FACADE[3]),
        "verge": (B_ROOF[0], B_EAVES, B_RIDGE[2]),
    }


def kind(p, index: int) -> str:
    """Tall (A) and low (B) bays alternate, starting with a tall one at the -X end.

    The first and the last house are end-of-terrace parts, marked L and R: their pavement
    runs on into the bookend beside them.
    """
    end = "L" if index == 0 else "R" if index == p.houses - 1 else ""
    return KINDS[index % 2] + end


def block(p, end: str = ""):
    """Ground block about X = 0: pavement on top, a joggled lap at each joint, the guide slot.

    A joint between two blocks is never a straight slit. A thin lower lap of each block
    reaches under its right-hand neighbour, so a house is put in after the one on its left:
    its facade, which stands over the left neighbour's pavement edge, and its block both come
    down from above. Seen from the front, the whole joint steps sideways and down behind the
    facades, so no line of sight passes along it either. The lap is thin, so the open joint
    below it never rises above the fixed rim in front. Below the lap the joint is wider,
    because the lower edge swings further along the street.

    `end` is "L" or "R" for the house at that end of the street: on that side the block has
    no lap but a plain edge that runs on to the bookend.
    """
    L = layout(p)
    hw = p.pitch / 2 - p.joint / 2
    y0, y1, bottom = L.block_y0, L.block_y1, L.block_z
    left_upper, upper = pavement_edges(p)  # the next block starts a joint on from `upper`
    lower = upper + p.joint + (p.lap - p.joint - 0.3)  # the lower lap's edge, under the neighbour
    left_lower = lower + p.joint + p.joint_flare - p.pitch
    core = hw - p.lap - p.jog
    inner = -(left_lower + p.jog) - 0.2  # the block's solid middle ends here on the left
    part = box(-inner, core, y0, y1, bottom, 0)
    if end == "L":
        part += box(L.edge_x0 - L.centres[0], -inner + 0.1, y0, y1, bottom, 0)
    if end == "R":
        part += box(core - 0.1, L.edge_x1 - L.centres[-1], y0, y1, bottom, 0)
    for front in (True, False):
        # Behind the facades the joint steps towards +X, so that the block with the lower lap
        # is also the wall behind the pavement joint. Stepping the other way would put the
        # open joint under the rear lap straight behind the pavement joint.
        shift = 0.0 if front else p.jog
        # underside of the part that lies over a lap; behind the facades it steps down
        level = bottom + p.lap_floor + p.lap_gap - (0.0 if front else p.lap_gap + 0.3)
        # the right side steps half a jog gap behind the line, the left side half a gap before
        if end != "R":
            a, b = (y0, JOG_Y + p.lap_gap / 2) if front else (JOG_Y + p.lap_gap / 2, y1)
            part += box(core - 0.1, upper + shift, a, b, level - p.lap_gap, 0)
            part += box(core - 0.1, lower + shift, a, b, bottom, level - p.lap_gap + 0.1)
        if end != "L":
            a, b = (y0, JOG_Y - p.lap_gap / 2) if front else (JOG_Y - p.lap_gap / 2, y1)
            part += box(left_upper + shift, -inner + 0.1, a, b, level, 0)
            part += box(left_lower + shift, -inner + 0.1, a, b, bottom, level + 0.1)
    if end != "R":
        # where the joint steps sideways, a small shaft would stay open from the pavement to
        # the underside: a tab on the lower lap reaches under it and closes it
        part += box(
            lower - 0.1,
            lower + p.joint + 0.2,
            JOG_Y - p.lap_gap / 2,
            JOG_Y + p.lap_gap / 2,
            bottom,
            bottom + p.lap_floor - p.lap_gap - 0.3,
        )
    # slot for the blade and the sled's tongue; a short land holds the unit along the street
    wide = slot_half_width(p)
    land = p.blade_width / 2 + p.pivot_gap / 2
    part -= box(-wide, wide, L.slot_y0, L.plate_y1 + 0.4, bottom - 1, 1)
    for side in (-1, 1):
        part += box(
            *sorted((side * land, side * (wide + 0.1))),
            L.slot_y0,
            L.blade_y1 + 0.2,
            L.pivot_z - 0.5,
            L.pivot_z + 0.5,
        )
    # notch for the rear panel's fin: the second point that holds the unit along the street
    wide = slot_half_width(p) - (p.blade_width - p.fin_width) / 2
    land = p.fin_width / 2 + p.pivot_gap / 2
    part -= box(-wide, wide, L.fin_y0 - 0.4, y1 + 1, bottom - 1, 1)
    for side in (-1, 1):
        part += box(
            *sorted((side * land, side * (wide + 0.1))),
            L.fin_y0 - 0.4,
            y1,
            L.pivot_z - 0.5,
            L.pivot_z + 0.5,
        )
    return part


def _house_a():
    hw, y0, y1, top = A_BODY
    part = box(-hw, hw, y0, y1, -0.1, top)
    hw, y0, y1, top = A_WINGS
    part += box(-hw, hw, y0, y1 + 0.1, WING_LIFT, top) + box(-OWN, OWN, y0, y1 + 0.1, -0.1, 1)
    hw, y0, y1, top = A_COPING
    part += box(-hw, hw, y0, y1 + 0.1, A_EAVES - 0.1, top)
    hw, y0, y1, top = A_ROOF
    part += box(-hw, hw, y0, y1, A_EAVES - 0.1, top)
    x0, x1, y0, y1, top = A_CHIMNEY
    return part + box(x0, x1, y0, y1, A_ROOF[3] - 0.1, top)


def _house_b():
    hw, y0, y1, top = B_BODY
    part = box(-hw, hw, y0, y1, -0.1, top)
    hw, y0, y1, top = B_FACADE
    part += box(-hw, hw, y0, y1 + 0.1, WING_LIFT, top) + box(-OWN, OWN, y0, y1 + 0.1, -0.1, 1)
    hw, y0, y1 = B_ROOF
    r0, r1, ridge = B_RIDGE
    part += prism_x(
        [(y0, B_EAVES - 0.1), (y1, B_EAVES - 0.1), (y1, B_EAVES + 1.2), (r1, ridge), (r0, ridge)],
        -hw,
        hw,
    )
    x0, x1, y0, y1, top = B_CHIMNEY
    return part + box(x0, x1, y0, y1, ridge - 0.5, top)


def house(p, which: str):
    """Ground block with its house volume, about X = 0, as one solid.

    `which` is a kind from `kind`: A or B, with L or R for the two end-of-terrace houses.
    The house is hollow over the guide slot, where the blade and the sled's tongue rise into it.
    """
    L = layout(p)
    part = block(p, which[1:]) + (_house_a() if which[0] == "A" else _house_b())
    wide = slot_half_width(p)
    return part - box(-wide, wide, L.slot_y0, L.plate_y1 + 0.4, -0.2, slot_top(p))
