"""Nikisz massing: the space each house may fill, on its ground block.

These are stand-ins for the decorated houses of the full design, drawn as the largest plain
volumes that the motion proof shows to be free of collision: tall bays (A) stand proud with
wings that lap in front of the low bays (B), so the joint between two houses is never a gap.
The ground block under each house is real: it carries the pavement, laps under its
neighbour, and holds the unit along the street on the blade that passes through it.
"""

from fala._layout import layout
from fala._parts import box, prism_x


def slot_half_width(p) -> float:
    """Half width of the guide slot through block and house: the blade plus the unit's swing."""
    L = layout(p)
    swing = (L.pivot_z - L.block_z) * L.cam.eccentricity * L.cam.k
    return p.blade_width / 2 + swing + 0.5


KINDS = ("A", "B")

# Tall bay: (half width, front, back, top) of each volume above the pavement.
A_BODY = (8.0, -1.2, 32.0, 36.0)
A_WINGS = (12.3, -3.3, -1.2, 36.0)  # facade plate with plinth and pilasters
A_COPING = (12.9, -3.9, -1.2, 37.8)  # from the eaves up
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


def kind(index: int) -> str:
    """Tall and low bays alternate, starting with a tall one at the -X end."""
    return KINDS[index % 2]


def block(p):
    """Ground block about X = 0: pavement on top, a joggled lap at each joint, the guide slot.

    A joint between two blocks is never a straight slit. Seen from above, the upper half of a
    block reaches over its right-hand neighbour and the lower half under its left-hand one.
    Seen from the front, the whole joint steps sideways and down behind the facades, so no
    line of sight passes along it either. Below the lap the joint is wider, because the lower
    edge swings further along the street.
    """
    L = layout(p)
    hw = p.pitch / 2 - p.joint / 2
    low = hw - p.joint_flare / 2
    y0, y1, bottom = L.block_y0, L.block_y1, L.block_z
    core = hw - p.lap - p.jog
    part = box(-core, core, y0, y1, bottom, 0)
    for front in (True, False):
        shift = 0.0 if front else p.jog
        level = bottom / 2 - (0.0 if front else 2 * p.lap_gap)
        # the right side ends half a jog gap behind the step, the left side half a gap before
        a, b = (y0, JOG_Y + p.lap_gap / 2) if front else (JOG_Y + p.lap_gap / 2, y1)
        part += box(core - 0.1, hw + p.lap / 2 + shift, a, b, level, 0)
        part += box(core - 0.1, low - p.lap / 2 + shift, a, b, bottom, level + 0.1)
        a, b = (y0, JOG_Y - p.lap_gap / 2) if front else (JOG_Y - p.lap_gap / 2, y1)
        part += box(-hw + p.lap / 2 + shift, -core + 0.1, a, b, level - p.lap_gap, 0)
        part += box(-low - p.lap / 2 + shift, -core + 0.1, a, b, bottom, level - p.lap_gap + 0.1)
    # slot for the blade and the sled's tongue; a short land holds the unit along the street
    wide = slot_half_width(p)
    land = p.blade_width / 2 + p.pivot_gap / 2
    part -= box(-wide, wide, L.blade_y0 - 0.6, L.plate_y1 + 0.4, bottom - 1, 1)
    for side in (-1, 1):
        part += box(
            *sorted((side * land, side * (wide + 0.1))),
            L.blade_y0 - 0.6,
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

    The house is hollow over the guide slot, where the blade and the sled's tongue rise into it.
    """
    L = layout(p)
    part = block(p) + (_house_a() if which == "A" else _house_b())
    wide = slot_half_width(p)
    top = max(L.blade_z, L.tongue_z + p.amplitude) + 1.5
    return part - box(-wide, wide, L.blade_y0 - 0.6, L.plate_y1 + 0.4, -0.2, top)
