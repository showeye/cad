"""Stand-in for the room: the kitchen of the approved concept as flat-colour massing.

Not product geometry. It stands in the motion proof so that the reveal can be judged and so that
the wings are checked against something of the room's real size. It is clipped to the space the
real room may fill (the hollow less `stage_gap`, clear of both hinges). The room is modelled in
the next stage; the details that break the print rules of the look brief are left out here.
Units: mm.
"""

from build123d import Cone, Cylinder, Pos, Rot, Sphere

from serce import _heart as heart
from serce import _shell as shell
from serce._heart import LEFT, RIGHT
from serce._solid import block, solids_of

WALL_Y = 13.0  # front face of the room's back wall


def _items(p):
    """(colour, solid) of every object, drawn for a floor at FLOOR_Z and a wall at WALL_Y."""
    f, w = heart.FLOOR_Z, WALL_Y
    out = []

    def add(colour, solid):
        out.append((colour, solid))

    def box(x0, x1, y0, y1, z0, z1):
        return block((x0, x1), (y0, y1), (z0, z1))

    add("honey", box(-60, 60, w, w + 1.5, f - p.floor_thick, 90))  # back wall
    add("tile", box(-60, 60, -40, w, f - p.floor_thick, f))  # floor
    # tiled stove with iron top, upstand, pipe, fire door with the fire showing, and a pot
    add("tile", box(-17.5, -6.5, 4.5, w, f, f + 12.5))
    add("coal", box(-18.2, -5.8, 3.8, w, f + 12.5, f + 13.6))
    add("tile", box(-17.5, -6.5, 10.2, w, f + 13.6, f + 21))
    add("coal", box(-15.5, -10.5, 3.9, 4.6, f + 1.6, f + 6.0))
    add("honey", box(-14.6, -11.4, 3.5, 4.0, f + 2.4, f + 3.9))
    add("coal", Pos(-9.2, 11.0, f + 27) * Cylinder(1.6, 12.5))
    add("bone", Pos(-13.2, 8.2, f + 15.4) * Cylinder(2.7, 3.6))
    add("coal", Pos(-13.2, 8.2, f + 17.5) * Cylinder(3.0, 0.7))
    # coal box in front of the stove, heaped
    add("coal", box(-15.8, -10.6, -2.6, 2.0, f, f + 3.4))
    for dx, dy, r in ((-14.4, -1.2, 1.5), (-12.2, 0.4, 1.6), (-13.3, -0.6, 1.9)):
        add("coal", Pos(dx, dy, f + 3.6) * Sphere(r))
    # white dresser with a glazed upper part that glows
    add("bone", box(6.0, 18.5, 6.0, w, f, f + 13))
    add("bone", box(5.4, 19.1, 5.4, w, f + 13, f + 14))
    add("bone", box(6.6, 18.0, 9.0, w, f + 14, f + 30))
    add("bone", box(6.0, 18.6, 8.4, w, f + 30, f + 31.4))
    for x0, x1 in ((7.5, 11.8), (12.8, 17.1)):
        add("honey", box(x0, x1, 8.4, 9.0, f + 18.2, f + 28.4))
        add("coal", box(x0 + 1.4, x1 - 1.4, 5.4, 6.0, f + 2.0, f + 11.2))
    # table with a crocheted cloth and a cake, and a stool
    add("bone", Pos(0.5, -4.5, f + 6.6) * Cone(8.6, 7.4, 4.2))
    add("bone", Pos(0.5, -4.5, f + 9.0) * Cylinder(7.4, 0.8))
    add("coal", Pos(0.5, -4.5, f + 2.3) * Cylinder(1.6, 4.6))
    add("tile", Pos(0.5, -4.5, f + 10.2) * Cylinder(3.0, 1.6))
    add("bone", box(9.6, 13.6, -9.5, -5.5, f, f + 4.4))
    # window in the left lobe with geraniums on the sill
    add("bone", box(-30.5, -15.5, w - 0.9, w, f + 21.5, f + 37.5))
    for x0, x1 in ((-29.3, -23.6), (-22.4, -16.7)):
        for z0, z1 in ((f + 22.7, f + 28.6), (f + 29.8, f + 33.0)):
            add("coal", box(x0, x1, w - 1.4, w - 0.9, z0, z1))
    add("bone", box(-31.2, -14.8, w - 2.6, w, f + 20.3, f + 21.5))
    for x in (-27.5, -23.0, -18.5):
        add("tile", Pos(x, w - 1.5, f + 23.0) * Sphere(1.5))
    # embroidered hanging over the table, a clock and a picture in the right lobe
    add("bone", box(-6.5, 5.5, w - 0.6, w, f + 17, f + 25))
    add("tile", box(-5.3, 4.3, w - 1.0, w - 0.6, f + 18.2, f + 19.0))
    add("tile", box(-5.3, 4.3, w - 1.0, w - 0.6, f + 23.0, f + 23.8))
    add("coal", Pos(26.5, w - 0.45, f + 31.5) * Rot(90, 0, 0) * Cylinder(4.2, 0.9))
    add("bone", Pos(26.5, w - 1.2, f + 31.5) * Rot(90, 0, 0) * Cylinder(3.2, 0.6))
    add("coal", box(23.0, 30.0, w - 0.9, w, f + 20.0, f + 25.0))
    add("bone", box(23.9, 29.1, w - 1.4, w - 0.9, f + 20.9, f + 24.1))
    return out


def room(p) -> dict:
    """Named solids of the stand-in room, one or more per colour: {name: (colour, solid)}."""
    h = heart.hinge(p)
    split = heart.FLOOR_Z - p.floor_thick
    space = {side: shell.stage(p, side, [heart.above(split)]) for side in (LEFT, RIGHT)}
    swing = [shell.hinge_tools(p, h, side)["swing"] for side in (LEFT, RIGHT)]
    placed = []  # (colour, solid); a later object is cut out of earlier ones of another colour
    for colour, solid in _items(p):
        new = []
        for side in (LEFT, RIGHT):
            for piece in solids_of(solid & space[side]):
                new += solids_of(piece - swing[0] - swing[1])
        kept = []
        for other, body in placed:
            if other != colour:
                for piece in new:
                    body = body - piece
            kept += [(other, s) for s in solids_of(body)]
        placed = kept + [(colour, s) for s in new]
    by_colour = {}
    for colour, solid in placed:
        by_colour.setdefault(colour, []).append(solid)
    out = {}
    for colour, solids in by_colour.items():
        merged = solids[0]
        for solid in solids[1:]:
            merged = merged + solid
        found = sorted(solids_of(merged), key=lambda s: (-round(s.volume, 3), tuple(s.center())))
        for i, solid in enumerate(found):
            out[f"reference_room_{colour}_{i:02d}"] = (colour, solid)
    return out
