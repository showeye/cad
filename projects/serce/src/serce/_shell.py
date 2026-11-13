"""The shell: two wings (front quarters) and the fixed back half, with the hinge on each flank.

Everything is built closed. A wing is one printed part in two colours, so it is returned as two
solids that touch: the coal body (wall, barrel, heel, root, lever, crank pin) and the lining.
The back half likewise: coal (wall, knuckles, the cellar block under the floor) and lining.

Seams. The outer `seam_depth` of the coal wall stops `seam_gap / 2` short of each seam plane, so
the closed heart shows a groove of `seam_gap`, like the false cracks. Deeper in, wall and lining
run up to the seam plane between front and back, where wing and back half touch: that face is
the seat that sets the closed position. At the centre plane the two wings stay
`centre_clearance` apart, so that they cannot hold each other off their seats.
"""

import math

from build123d import Edge, Face, Plane, Pos, Rot, Wire, extrude

from serce import _heart as heart
from serce._heart import LEFT, RIGHT
from serce._solid import cut, fuse, one, rod, slab


def lever_levels(p) -> tuple[float, float, float]:
    """Local z of the lever's top, the lever's bottom and the crank pin's end."""
    top = -(p.roof + p.lever_clear)
    return top, top - p.lever_thick, top - p.lever_thick - p.crank_len


def pocket_radius(p) -> float:
    """Radius about the hinge axis that the wing's heel sweeps, plus the hinge gap."""
    return math.hypot(p.heel_reach, p.heel) + p.hinge_gap


def swing_radius(p) -> float:
    """Nothing fixed inside the heart comes nearer to a hinge axis than this.

    It is just the heel's sweep, so the cellar stands over the clearance round the root's
    collar and over the keyhole."""
    return pocket_radius(p)


def _mirror(shape, side: int):
    return shape if side == LEFT else shape.mirror(Plane.YZ)


def lever_outline(p, grow: float, z0: float, z1: float):
    """The lever's arm in its own frame, x from the hinge axis to the crank pin, grown by `grow`.

    The arm leaves the root as a neck on one side (y <= 0) and widens to the crank pin. At
    assembly the lever passes down a keyhole in the bed that has this outline. The neck keeps
    the keyhole under the back half and the cellar, which cover it: it reaches neither past
    the flank at the back nor into the strip the wing's wall stands over at the front.
    """
    half = p.lever_width / 2 + grow
    # one outline: from the root, a straight edge tangent to the round end, the end, and back
    reach = math.hypot(p.lever, grow)
    lean = math.atan2(-grow, p.lever) + math.asin(half / reach)
    run = math.sqrt(reach**2 - half**2)
    start, low = (0.0, grow, 0.0), (0.0, -p.lever_neck - grow, 0.0)
    flare = (4.0, -half, 0.0)
    touch = (run * math.cos(lean), grow + run * math.sin(lean), 0.0)
    edges = [
        Edge.make_line(start, touch),
        Edge.make_three_point_arc(touch, (p.lever + half, 0.0, 0.0), (p.lever, -half, 0.0)),
        Edge.make_line((p.lever, -half, 0.0), flare),
        Edge.make_line(flare, low),
        Edge.make_line(low, start),
    ]
    return Pos(0, 0, z0) * extrude(Face(Wire(edges)), amount=z1 - z0, dir=(0, 0, 1))


def hinge_tools(p, h: heart.Hinge, side: int) -> dict:
    """Solids about the hinge axis of `side`, in world coordinates."""
    f, r, gap = h.frame, p.hinge_radius, p.hinge_gap
    lever_top, lever_bottom, crank_end = lever_levels(p)
    closed = 180 + p.wing_max / 2  # direction of the lever in the local frame, wings closed
    arm = Rot(0, 0, closed) * lever_outline(p, 0.0, lever_bottom, lever_top)
    crank = (
        Rot(0, 0, closed)
        * Pos(p.lever, 0, 0)
        * rod(Plane.XY, p.crank_d / 2, crank_end, lever_bottom)
    )
    # the cove of the barrel, and behind it the pocket the heel swings in. The pocket is lower
    # than the barrel, so the barrel blocks every straight line through the hinge.
    pocket = rod(f, r + gap, -1.0, h.barrel_top + gap / 2) + (
        rod(f, pocket_radius(p), -1.0, h.barrel_top + gap / 2)
        & slab(f, (-gap, 20), (-20, p.heel + gap), (-2.0, h.barrel_top + gap))
    )
    tools = {
        # turning with the wing
        "barrel": rod(f, r, 0.0, h.barrel_top),
        # the root: a collar that runs on a shoulder in the bed, and a journal below it
        "root": rod(f, p.root_radius, -p.collar_depth, 0.0)
        + rod(f, p.journal_radius, lever_bottom - p.root_boss, -p.collar_depth + 0.1),
        "lever": f.location * arm,
        "crank": f.location * crank,
        "bore": rod(f, (p.pin_d + p.pin_clear) / 2, crank_end - 1, h.barrel_top + 1),
        # cut from the wing
        "knuckle_room": rod(f, r + gap, h.barrel_top + gap / 2, h.knuckle_top + 1),
        "knuckle_collar": rod(f, r + gap + 0.8, h.barrel_top - 0.5, h.knuckle_top + 1),
        # fixed, on the back half
        "knuckle": rod(f, r, h.barrel_top + gap, h.knuckle_top),
        "knuckle_bore": rod(f, (p.pin_d + p.pin_clear) / 2, h.barrel_top, pin_top(p, h) + 0.5),
        # cut from the back half: the cove of the barrel and the pocket the heel swings in
        "pocket": pocket,
        # cut from everything that stands inside the heart
        "swing": rod(f, swing_radius(p), -1.0, h.knuckle_top + 1),
    }
    return {name: _mirror(shape, side) for name, shape in tools.items()}


def pin_top(p, h: heart.Hinge) -> float:
    """Local z of the top end of the hinge pin, inside the fixed knuckle."""
    return pin_bottom(p) + p.pin_length


def pin_bottom(p) -> float:
    """Local z of the lower end of the hinge pin: it stands out below the root pad for pliers."""
    return lever_levels(p)[1] - p.root_boss - p.pad_gap - p.pad_thick - p.pin_grip


def centre_rim(p, side: int) -> float:
    """Distance from the centre plane at which the inner part of the wing's rim ends.

    The left wing's rim runs to the centre plane and, with a lap, on across it; the right
    wing's rim is cut back for it.
    """
    if side == LEFT:
        return 0.0
    return p.tongue + p.centre_clearance


def wing(p, side: int) -> dict:
    """Coal body and lining of the wing on `side`, closed."""
    h = heart.hinge(p)
    tool = hinge_tools(p, h, side)
    g = p.seam_gap / 2
    foot = heart.along_axis(h, side, z0=p.bed_gap)
    sill = heart.along_axis(h, side, z0=p.bed_gap + p.sill)
    front = heart.in_front(0.0)
    # all wall material of the front quarter: the outer layer stops short of both seam planes,
    # the rest runs up to the seam plane at the back and to the wing's rim at the centre
    outer = heart.skin(p, side, 0.0, [heart.beside(side, g), heart.in_front(-g), *foot])
    inner = heart.skin(
        p, side, p.seam_depth, [heart.beside(side, centre_rim(p, side)), front, *foot]
    )
    # the wall runs back past the seam plane as a heel along the barrel, so the barrel has a root
    heel = heart.skin(
        p,
        side,
        0.0,
        [
            *heart.along_axis(h, side, z0=p.bed_gap, z1=h.barrel_top),
            *heart.hinge_box(h, side, x=(0.0, p.heel_reach), y=(0.0, p.heel)),
        ],
    )
    shell_parts = [outer, inner, heel]
    hollows = [heart.hollow(p, side, p.wall + p.lining)]
    # the lining starts a sill above the foot, so no honey shows through the gap over the bed
    cores = [heart.hollow(p, side, p.wall, sill)]
    if side == LEFT and p.tongue:
        # Lap at the centre seam: the inner part of the left wing's wall and its lining run on
        # across the centre plane under the right wing's outer layer. The wings part square to
        # the centre plane, so the lap slides straight out, and a line of sight into the seam
        # groove ends on coal.
        across = [((1.0, 0.0, 0.0), p.tongue), front]
        shell_parts.append(heart.skin(p, RIGHT, p.seam_depth + p.tongue_clear, [*across, *foot]))
        hollows.append(heart.hollow(p, RIGHT, p.wall + p.lining))
        cores.append(heart.hollow(p, RIGHT, p.wall, [*across, *sill]))
    recess = None
    if side == RIGHT and p.tongue:
        # room for the left wing's lap: behind the outer layer the right wing's rim is cut back
        recess = heart.skin(p, RIGHT, p.seam_depth, [((1.0, 0.0, 0.0), centre_rim(p, RIGHT))])
    wall = cut(fuse(*shell_parts), *hollows, tool["knuckle_room"], recess, what="wing wall")
    # the lining keeps clear of the knuckle, so the hole round the knuckle is coal all through
    lining = cut(
        fuse(*[one(wall & core, "wing lining") for core in cores], what="wing lining"),
        tool["barrel"],
        tool["bore"],
        tool["knuckle_collar"],
        what="wing lining",
    )
    coal = fuse(
        cut(wall, lining, what="wing coal"),
        tool["barrel"],
        tool["root"],
        tool["lever"],
        tool["crank"],
        what="wing coal",
    )
    return {"coal": cut(coal, tool["bore"], what="wing coal"), "lining": lining}


def back(p) -> dict:
    """Coal body and lining of the fixed back half, with the cellar block under the floor."""
    h = heart.hinge(p)
    g = p.seam_gap / 2
    split = heart.FLOOR_Z - p.floor_thick  # the cellar's top: below it everything is coal
    coal, lining = [], []
    for side in (LEFT, RIGHT):
        tool = hinge_tools(p, h, side)
        foot = heart.along_axis(h, side, z0=p.bed_gap)
        on_bed = heart.along_axis(h, side, z0=0.0)
        outer = heart.skin(p, side, 0.0, [heart.behind(g), *foot])
        # behind the groove the wall stands on the bed: no line of sight under the back half
        inner = heart.skin(p, side, p.seam_depth, [heart.behind(0.0), *on_bed])
        wall = cut(fuse(outer, inner), heart.hollow(p, side, p.wall), what="back wall")
        # below the floor the lining's place and the hollow are one coal block: the cellar
        low = heart.hollow(p, side, p.wall, [heart.behind(0.0), heart.below(split), *on_bed])
        front = heart.hollow(
            p,
            side,
            p.wall + p.lining + p.stage_gap,
            [heart.in_front(0.0), heart.below(split), *on_bed],
        )
        knuckle = one(
            tool["knuckle"] & heart.skin(p, side, -h.proud, heart.along_axis(h, side, z0=0.0)),
            "knuckle",
        )
        coal += [
            cut(wall, tool["pocket"], what="back wall"),
            cut(low, tool["pocket"], tool["swing"], what="cellar"),
            cut(front, tool["swing"], what="cellar front"),
            knuckle,
        ]
        skin_in = heart.hollow(p, side, p.wall, [heart.behind(0.0), heart.above(split)])
        lining.append(
            cut(
                skin_in,
                heart.hollow(p, side, p.wall + p.lining),
                tool["pocket"],
                tool["knuckle"],
                tool["knuckle_bore"],
                what="lining",
            )
        )
    body = fuse(*coal, what="back")
    for side in (LEFT, RIGHT):
        body = cut(body, hinge_tools(p, h, side)["knuckle_bore"], what="back")
    return {"coal": body, "lining": fuse(*lining, what="back lining")}


def stage(p, side: int, extra=()):
    """The space fixed things may fill inside the heart on `side`: the hollow less a clearance."""
    return heart.hollow(p, side, p.wall + p.lining + p.stage_gap, extra)
