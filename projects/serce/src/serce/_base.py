"""The base: coal bed, slider, pusher, chassis, cam disc, grip ring, foot, and bought hardware.

Everything is built for the closed position (turn = 0). Units: mm, degrees.

Stack, top to bottom: coal bed (hollow, on two legs) / pusher bar on the slider / chassis plate
with a hub down through the ring / cam disc / floor of the grip ring / steel washer in the foot.
The bed's two main facets are square to the hinge axes, so the wings sweep just above them.
"""

import math
from dataclasses import dataclass

from build123d import Cone, Cylinder, Plane, Polygon, Pos, Rot, extrude
from cadkit.features.mechanical import cam_groove, hex_prism
from cadkit.features.polyhedron import halfspace_solid

from serce import _heart as heart
from serce import _kinematics as kin
from serce import _shell as shell
from serce._heart import LEFT, RIGHT
from serce._solid import block, cut, fuse, one, rod

SIDES_20 = 20
INSERT_D, INSERT_LEN = 4.2, 4.0  # M3 heat-set insert, short type (verify against datasheet)
M3_CLEAR, M3_HEAD_D, M3_HEAD_H = 3.4, 6.0, 2.4
M4_CLEAR, M4_HEAD_D, M4_HEAD_H = 4.4, 7.6, 2.2  # ISO 7380 button head
M4_NUT_AF, M4_NUT_H = 7.0, 3.2  # ISO 4032
MAGNET_D, MAGNET_H = 5.0, 2.0  # N35 disc magnet (verify pull against datasheet)
MAGNET_R, MAGNET_ANGLES = 27.0, (30.0, 90.0, 150.0)  # on the cam disc, clear of the groove
WASHER_ID, WASHER_OD = 26.0, 72.0  # M24 fender washer, ISO 7093-1 (DIN 9021), 5 mm thick
FOOT_D, FOOT_H = 8.0, 1.6  # self-adhesive silicone bumper
SPRING_OD, SPRING_ID = 4.5, 3.5
CONTACT = 0.002  # the crank pins rest on the pusher; modelled this far apart, so that the
# line contact of a round pin on a flat plate never counts as an overlap
BACK_SCREWS_Y = (-12.0, 15.0)  # on the ridge line, clear of the levers' sweep
LEG_X, LEG_W, LEG_Y = 19.5, 6.0, 20.0  # legs of the bed: inner face, width, half length


@dataclass(frozen=True)
class Levels:
    """World z of the layers of the base."""

    bed: float  # underside of the coal bed
    ring_top: float
    slider_top: float
    slider_bottom: float  # = chassis top
    chassis_bottom: float
    cam_top: float
    cam_bottom: float
    web_top: float
    web_bottom: float
    wall_bottom: float  # bottom edge of the grip ring's wall; its floor stands lower
    neck_top: float  # the ring's neck inside the bed's skirt
    shoulder: float  # top of the ring's wall outside the neck
    washer_top: float
    washer_bottom: float
    foot_bottom: float
    hub_bottom: float  # shoulder of the chassis hub on the foot's boss


def levels(p) -> Levels:
    slider_bottom = p.slider_top - p.slider_thick
    chassis_bottom = slider_bottom - p.chassis_thick
    cam_top = chassis_bottom - 0.4
    cam_bottom = cam_top - p.cam_thick
    web_top = cam_bottom - 0.1
    web_bottom = web_top - p.web_thick
    washer_top = web_bottom - 0.3  # the ring runs on a narrow land near the hub
    washer_bottom = washer_top - p.ballast_thick
    return Levels(
        bed=p.base_z,
        ring_top=p.base_z - p.ring_gap,
        slider_top=p.slider_top,
        slider_bottom=slider_bottom,
        chassis_bottom=chassis_bottom,
        cam_top=cam_top,
        cam_bottom=cam_bottom,
        web_top=web_top,
        web_bottom=web_bottom,
        wall_bottom=web_bottom + 0.3 + p.ring_gap,
        neck_top=p.base_z - p.ring_gap,
        shoulder=p.base_z - p.skirt - p.ring_gap,
        washer_top=washer_top,
        washer_bottom=washer_bottom,
        foot_bottom=washer_bottom - p.foot_floor,
        hub_bottom=washer_top - 0.4,
    )


def _hs(planes, what: str):
    solid = halfspace_solid([n for n, _ in planes], [d for _, d in planes])
    if solid is None:
        raise ValueError(f"{what}: planes enclose nothing")
    return solid


def _polygon_sides(apothem: float, sides: int = SIDES_20):
    out = []
    for k in range(sides):
        t = 2 * math.pi * (k + 0.5) / sides
        out.append(((math.cos(t), math.sin(t), 0.0), apothem))
    return out


def _mirror(shape, side: int):
    return shape if side == LEFT else shape.mirror(Plane.YZ)


def ridge_z(p) -> float:
    """Height of the bed's ridge, where its two main facets meet."""
    return heart.hinge(p).seat / heart.V_DIR[2]


def bed_radius(p) -> float:
    return p.ring_r - 0.6


def lever_plane(p, drop: float):
    """Half-space below the levers' underside by `drop` on each side: two planes."""
    h = heart.hinge(p)
    z = shell.lever_levels(p)[1] - drop
    return [heart.along_axis(h, side, z1=z)[0] for side in (LEFT, RIGHT)]


# ---------------------------------------------------------------- coal bed
def _bed_planes(p, inset: float, bottom: float):
    """The mound as half-spaces, every face moved in by `inset` (the bottom plane is given)."""
    h = heart.hinge(p)
    slope = math.radians(p.bed_gable)
    planes = [((0.0, 0.0, -1.0), -bottom)]
    planes += [(n, d - inset) for n, d in _polygon_sides(bed_radius(p))]
    for side in (LEFT, RIGHT):
        n, d = heart.along_axis(h, side, z1=0.0)[0]
        planes.append((n, d - (p.roof if inset else 0.0)))
    for sy in (1, -1):
        n = (0.0, sy * math.sin(slope), math.cos(slope))
        d = math.sin(slope) * p.bed_ridge + math.cos(slope) * ridge_z(p)
        planes.append((n, d - inset))
    return planes


def coal_bed(p):
    """Faceted mound with a low base slab, hollow under a roof that carries the two root bores."""
    h = heart.hinge(p)
    lv = levels(p)
    r = bed_radius(p)
    mound = _hs(_bed_planes(p, 0.0, lv.bed), "bed")
    # low slab that closes the grip ring from above; its rim is chamfered
    c = math.sqrt(0.5)
    slab_planes = [((0.0, 0.0, -1.0), -lv.bed), ((0.0, 0.0, 1.0), p.slab_top)]
    for n, d in _polygon_sides(r):
        slab_planes += [(n, d), ((c * n[0], c * n[1], c), c * (r - 0.8) + c * p.slab_top)]
    body = fuse(mound, _hs(slab_planes, "bed slab"), what="bed")
    body = cut(body, _hs(_bed_planes(p, p.bed_wall, lv.bed - 1.0), "bed hollow"), what="bed")
    # skirt round the ring's neck: no straight line of sight into the base
    skirt = _hs(
        [
            ((0.0, 0.0, -1.0), -(lv.bed - p.skirt)),
            ((0.0, 0.0, 1.0), lv.bed + 0.1),
            *_polygon_sides(r),
        ],
        "bed skirt",
    )
    body = fuse(
        body, skirt - rod(Plane.XY, neck_radius(p) + p.ring_gap, lv.bed - 5, lv.bed + 1), what="bed"
    )

    _lever_top, lever_bottom, _ = shell.lever_levels(p)
    pad_top = lever_bottom - p.root_boss - p.pad_gap
    pad_bottom = pad_top - p.pad_thick
    additions, removals = [], []
    for side in (LEFT, RIGHT):
        f = h.frame
        sx = side
        # legs down to the chassis; the slider runs between them
        roof = heart.along_axis(h, side, z1=-0.5)[0]
        x0, x1 = sorted((sx * LEG_X, sx * (LEG_X + LEG_W)))
        additions.append(
            _hs(
                [
                    ((-1.0, 0.0, 0.0), -x0),
                    ((1.0, 0.0, 0.0), x1),
                    ((0.0, -1.0, 0.0), LEG_Y),
                    ((0.0, 1.0, 0.0), LEG_Y),
                    ((0.0, 0.0, -1.0), -lv.slider_bottom),
                    roof,
                ],
                "bed leg",
            )
        )
        # thrust pad under the root, on a post from the roof, opposite the lever's sweep
        post_dir = p.wing_max / 2 - p.keyhole / 2  # opposite the middle of the lever's sweep
        reach = p.root_radius + p.journal_gap + 0.4
        pad = rod(Plane.XY, p.journal_radius + 0.6, pad_bottom, pad_top) & block(
            (-1.2, 10), (-10, 10), (pad_bottom, pad_top)
        )
        post = Rot(0, 0, post_dir) * (
            block((reach, reach + 3.0), (-1.3, 1.3), (pad_bottom, -p.roof + 1.0))
            + block((0.0, reach + 3.0), (-1.3, 1.3), (pad_bottom, pad_top))
        )
        additions.append(_mirror(f.location * (pad + post), side))
        # bore for the root, the keyhole the lever passes at assembly, the hole for the hinge pin
        slot_dir = 180 + p.wing_max / 2 - p.keyhole
        keyhole = Rot(0, 0, slot_dir) * shell.lever_outline(p, 0.4, -p.roof - 1.0, 1.0)
        # the bore: the root's collar runs on the shoulder, which carries the wing and closes
        # the running clearance to any line of sight
        removals += [
            _mirror(rod(f, p.root_radius + p.journal_gap, -p.collar_depth, 1.0), side),
            _mirror(rod(f, p.journal_radius + p.journal_gap, -p.roof - 1.0, 0.0), side),
            _mirror(f.location * keyhole, side),
            _mirror(rod(f, (p.pin_d + p.pin_clear) / 2, pad_bottom - 1.0, pad_top + 1.0), side),
        ]
    # screws from inside the bed up into the cellar of the back half; insert pockets for the
    # chassis screws in the legs
    seat = ridge_z(p) - p.roof / heart.V_DIR[2] + 1.0
    for y in BACK_SCREWS_Y:
        removals += [
            Pos(0, y, 0) * rod(Plane.XY, M3_CLEAR / 2, seat - 1.0, ridge_z(p) + 1.0),
            Pos(0, y, 0) * rod(Plane.XY, M3_HEAD_D / 2 + 0.3, seat - 6.0, seat),
        ]
    for sx in (-1, 1):
        removals.append(
            Pos(sx * (LEG_X + LEG_W / 2), 0, 0)
            * rod(
                Plane.XY, INSERT_D / 2, lv.slider_bottom - 0.5, lv.slider_bottom + INSERT_LEN + 0.6
            )
        )
    body = fuse(body, *additions, what="bed")
    return cut(body, *removals, what="bed")


def neck_radius(p) -> float:
    """Outer radius of the grip ring's neck, which stands up inside the bed's skirt."""
    return bed_radius(p) - 1.0 - p.ring_gap


def back_screw_seat(p) -> float:
    """World z of the seat of the screws that hold the back half."""
    return ridge_z(p) - p.roof / heart.V_DIR[2] + 1.0


# ---------------------------------------------------------------- slider and pusher
def yoke_x(p) -> tuple[float, float]:
    """Extent in |x| of the yoke plates: they cover the crank pin's path and clear the pad."""
    h = heart.hinge(p)
    _, lever_bottom, crank_end = shell.lever_levels(p)
    half = math.radians(p.wing_max / 2)
    outer = -h.point(-p.lever, 0, lever_bottom)[0] + 0.8
    pad_x = -h.point(-1.2, 0, lever_bottom - p.root_boss - p.pad_gap)[0]
    inner = pad_x + 0.5
    reach = -h.point(-p.lever * math.cos(half), 0, crank_end)[0]  # pin's inner end at the stops
    if inner > reach + 1.5:
        raise ValueError("Yoke plates cannot reach the crank pin at the ends of the swing")
    return inner, outer


def _yoke_plate(p, side: int, y0: float, y1: float, z0: float):
    inner, outer = yoke_x(p)
    x0, x1 = sorted((side * inner, side * outer))
    top = lever_plane(p, p.yoke_clear)[0 if side == LEFT else 1]
    return _hs(
        [
            ((-1.0, 0.0, 0.0), -x0),
            ((1.0, 0.0, 0.0), x1),
            ((0.0, -1.0, 0.0), -y0),
            ((0.0, 1.0, 0.0), y1),
            ((0.0, 0.0, -1.0), -z0),
            top,
        ],
        "yoke plate",
    )


def slider_half_width(p) -> float:
    return LEG_X - p.slide_gap


PUSHER_DEPTH = 6.0  # front to back
PUSHER_THICK = 2.2
RAIL_W = 2.6
BOSS_R = 3.0  # round the follower pin
BOSS_H = 4.0  # above the slider plate


def pusher_half_width(p) -> float:
    return slider_half_width(p) - RAIL_W - 0.15


def _rail(p, y0: float, y1: float, z: float):
    """Rail on the slider's +x edge; its lip leans over the pusher's chamfered edge."""
    w, pw = slider_half_width(p), pusher_half_width(p)
    top = PUSHER_THICK + 0.6
    profile = [(pw + 0.15, 0.0), (w, 0.0), (w, top), (pw - 1.0, top), (pw - 1.0, top - 0.3)]
    profile += [(pw + 0.15, 1.15)]
    face = Plane.XZ.offset(-y1) * Polygon(*profile, align=None)
    return Pos(0, 0, z) * extrude(face, amount=y1 - y0)


def spring_z(p) -> float:
    """Height of the pusher spring's axis: it lies in a shallow groove of the slider."""
    return p.slider_top + 1.2


def slider(p):
    """Plate between the bed's legs: front yoke plates, rails for the pusher, follower boss.

    Built with the wings closed: the slider has gone `over_travel` past the crank pins.
    """
    lv = levels(p)
    yc = kin.slider_y(p, 0.0)
    r = p.crank_d / 2
    w = slider_half_width(p)
    follower = yc + kin.follower_offset(p)
    rear = yc + r + p.yoke_gap + PUSHER_DEPTH + p.pusher_travel + 3.0
    top = lv.slider_top
    body = block((-w, w), (yc - r - p.plate - 1.0, rear), (lv.slider_bottom, top))
    body += block((-BOSS_R, BOSS_R), (rear - 1.0, follower), (lv.slider_bottom, top))
    body += Pos(0, follower, 0) * rod(Plane.XY, BOSS_R, lv.slider_bottom, top + BOSS_H)
    body += block((-BOSS_R, BOSS_R), (follower - BOSS_R, follower), (top - 0.5, top + BOSS_H))
    inner, outer = yoke_x(p)
    rail = _rail(p, yc + r + p.plate + 0.3, rear, top - 0.01)
    body += rail + rail.mirror(Plane.YZ)
    # the stop the spring presses the pusher against, and the end of the pusher's free travel
    stop = yc + r + p.yoke_gap
    body += block((-3.0, 3.0), (stop - 2.0, stop), (top - 0.5, top + PUSHER_THICK))
    end = stop + PUSHER_DEPTH + p.pusher_travel
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 8.0, sx * 11.0))
        body += block((x0, x1), (end, end + 2.0), (top - 0.5, top + PUSHER_THICK))
    for side in (LEFT, RIGHT):
        body += _yoke_plate(p, side, yc - r - p.plate, yc - r, top - 0.5)
        # pocket under the crank pin, which dips below the slider's top in mid-swing
        x0, x1 = sorted((side * inner, side * (outer + 0.6)))
        body -= block((x0, x1), (yc - r, yc + r + p.pusher_travel + 0.4), (top - 2.0, top + 1))
    # groove for the pusher spring, hole for the follower pin, spring peg on the boss
    half = SPRING_OD / 2 + 0.35
    body -= block(
        (-half, half), (yc + r + PUSHER_DEPTH - 0.5, follower - BOSS_R), (top - 1.3, top + 1)
    )
    body -= Pos(0, follower, 0) * rod(
        Plane.XY, p.follower_d / 2, lv.slider_bottom - 1, top + BOSS_H + 1
    )
    body += Pos(0, follower - BOSS_R, spring_z(p)) * Rot(90, 0, 0) * Cylinder(1.4, 3.0)
    return one(body, "slider")


def pusher(p):
    """Bar that the spring presses against the back of both crank pins. Built with wings closed."""
    lv = levels(p)
    y = kin.pin_y(p, 0.0) + p.crank_d / 2 + CONTACT
    pw = pusher_half_width(p)
    z0 = lv.slider_top + 0.15
    profile = [
        (-pw, 0.0),
        (pw, 0.0),
        (pw, 1.0),
        (pw - 1.15, PUSHER_THICK),
        (-pw + 1.15, PUSHER_THICK),
    ]
    profile += [(-pw, 1.0)]
    base = Plane.XZ.offset(-(y + PUSHER_DEPTH)) * Polygon(*profile, align=None)
    body = Pos(0, 0, z0) * extrude(base, amount=PUSHER_DEPTH)
    for side in (LEFT, RIGHT):
        body += _yoke_plate(p, side, y, y + p.plate, z0 + 0.5)
    body += Pos(0, y + PUSHER_DEPTH + 1.0, spring_z(p)) * Rot(90, 0, 0) * Cylinder(1.4, 3.0)
    # the levers' round ends swing over the corners of the bar: keep all of it under them
    under = [((0.0, 0.0, -1.0), 50.0), *lever_plane(p, p.yoke_clear)]
    under += [((sx, 0.0, 0.0), 50.0) for sx in (-1, 1)] + [((0.0, sy, 0.0), 80.0) for sy in (-1, 1)]
    return one(body & _hs(under, "pusher envelope"), "pusher")


def spring(p, turn: float):
    """Stand-in for the pusher spring at `turn`: a tube between the pusher and the follower boss."""
    y0 = kin.pin_y(p, turn) + p.crank_d / 2 + PUSHER_DEPTH + CONTACT
    length = spring_length(p, turn) - CONTACT
    tube = Cylinder(SPRING_OD / 2, length) - Cylinder(SPRING_ID / 2, length + 1)
    return Pos(0, y0 + length / 2, spring_z(p)) * Rot(90, 0, 0) * tube


def spring_length(p, turn: float) -> float:
    """Installed length of the pusher spring."""
    base = kin.follower_offset(p) - BOSS_R - p.yoke_gap - p.crank_d / 2 - PUSHER_DEPTH
    return base - kin.pusher_lag(p, turn)


# ---------------------------------------------------------------- chassis, cam, ring, foot
def chassis(p):
    """Plate inside the ring; hub down through cam disc and ring floor; the slider runs on it."""
    lv = levels(p)
    r = p.ring_r - p.ring_wall - 0.5
    body = Pos(0, 0, (lv.slider_bottom + lv.chassis_bottom) / 2) * Cylinder(r, p.chassis_thick)
    body += rod(Plane.XY, p.hub_r, lv.hub_bottom, lv.chassis_bottom + 0.1)
    body += Pos(0, 0, lv.hub_bottom - 1.25) * hex_prism(5.5, 2.7)
    # slot for the follower pin
    e, half = kin.stroke(p) / 2, p.follower_d / 2 + 0.25
    y0, y1 = p.groove_radius - e, p.groove_radius + e
    body -= block((-half, half), (y0, y1), (lv.chassis_bottom - 1, lv.slider_bottom + 1))
    for y in (y0, y1):
        body -= Pos(0, y, 0) * rod(Plane.XY, half, lv.chassis_bottom - 1, lv.slider_bottom + 1)
    # tie screw and its nut, screws up into the legs of the bed
    body -= rod(Plane.XY, M4_CLEAR / 2, lv.hub_bottom - 4, lv.slider_bottom + 1)
    nut = hex_prism((M4_NUT_AF + 0.2) / math.sqrt(3), M4_NUT_H + 0.2)
    body -= Pos(0, 0, lv.slider_bottom - (M4_NUT_H + 0.2) / 2 + 0.01) * nut
    for sx in (-1, 1):
        x = sx * (LEG_X + LEG_W / 2)
        body -= Pos(x, 0, 0) * rod(
            Plane.XY, M3_CLEAR / 2, lv.chassis_bottom - 1, lv.slider_bottom + 1
        )
        body -= Pos(x, 0, lv.chassis_bottom + 0.84) * Cone(M3_HEAD_D / 2, M3_CLEAR / 2, 1.7)
    return one(body, "chassis")


def magnet_positions(radius: float = MAGNET_R):
    return [
        (radius * math.cos(math.radians(a)), radius * math.sin(math.radians(a)))
        for a in MAGNET_ANGLES
    ]


def cam_disc(p):
    """Disc with the cam groove; coupled to the grip ring by magnets (the slipping clutch)."""
    lv = levels(p)
    r = p.ring_r - p.ring_wall - 0.5
    body = Pos(0, 0, (lv.cam_top + lv.cam_bottom) / 2) * Cylinder(r, p.cam_thick)
    body -= rod(Plane.XY, p.hub_r + 0.25, lv.cam_bottom - 1, lv.cam_top + 1)
    body -= Pos(0, 0, lv.cam_top) * cam_groove(
        lambda turn: kin.follower_y(p, turn), p.follower_d + p.groove_clear, p.groove_depth
    )
    for x, y in magnet_positions():
        body -= Pos(x, y, 0) * rod(
            Plane.XY, MAGNET_D / 2 + 0.05, lv.cam_bottom - 1, lv.cam_bottom + MAGNET_H
        )
    return one(body, "cam disc")


def grip_ring(p):
    """Faceted ring with a floor: the part the hand turns.

    Its neck stands up inside the bed's skirt and its floor stands down inside the foot's rim,
    so neither gap gives a straight view of the inside.
    """
    lv = levels(p)
    c = math.sqrt(0.5)
    planes = [((0.0, 0.0, 1.0), lv.shoulder), ((0.0, 0.0, -1.0), -lv.wall_bottom)]
    for n, d in _polygon_sides(p.ring_r):
        planes.append((n, d))
        for sign, z in ((1, lv.shoulder), (-1, lv.wall_bottom)):
            planes.append(((c * n[0], c * n[1], sign * c), c * (p.ring_r - 1.0) + sign * c * z))
    body = _hs(planes, "grip ring")
    body += rod(Plane.XY, neck_radius(p), lv.shoulder - 0.5, lv.neck_top)
    body += rod(Plane.XY, WASHER_OD / 2, lv.web_bottom, lv.wall_bottom + 0.5)
    body -= rod(Plane.XY, p.ring_r - p.ring_wall, lv.web_top, lv.neck_top + 1)
    body -= rod(Plane.XY, p.hub_r + 0.25, lv.web_bottom - 1, lv.web_top + 1)
    # narrow land that runs on the steel washer
    body += rod(Plane.XY, WASHER_ID / 2 + 4.5, lv.washer_top, lv.web_bottom + 0.1) - rod(
        Plane.XY, WASHER_ID / 2 + 0.8, lv.washer_top - 1, lv.web_bottom + 1
    )
    for x, y in magnet_positions():
        body -= Pos(x, y, 0) * rod(
            Plane.XY, MAGNET_D / 2 + 0.05, lv.web_top - MAGNET_H, lv.web_top + 1
        )
    return one(body, "grip ring")


def foot_radius(p) -> float:
    return p.ring_r - 0.6


def foot(p):
    """Tray under the ring: holds the ballast washer, takes the tie screw, carries the feet."""
    lv = levels(p)
    r = foot_radius(p)
    rim_top = lv.wall_bottom - p.ring_gap
    body = rod(Plane.XY, r, lv.foot_bottom, rim_top)
    body -= rod(Plane.XY, WASHER_OD / 2 + 0.3, lv.washer_bottom, rim_top + 1)
    body += rod(Plane.XY, WASHER_ID / 2 - 0.4, lv.washer_bottom - 0.1, lv.hub_bottom)
    body -= Pos(0, 0, lv.hub_bottom - 1.25) * hex_prism(5.5 + 0.15, 2.7)
    body -= rod(Plane.XY, M4_CLEAR / 2, lv.foot_bottom - 1, lv.hub_bottom + 1)
    body -= rod(Plane.XY, M4_HEAD_D / 2 + 0.3, lv.foot_bottom - 1, lv.foot_bottom + M4_HEAD_H + 0.3)
    for x, y in feet_positions(p):
        body -= Pos(x, y, 0) * rod(
            Plane.XY, FOOT_D / 2 + 0.3, lv.foot_bottom - 1, lv.foot_bottom + 0.3
        )
    return one(body, "foot")


def feet_positions(p):
    r = foot_radius(p) - 7.0
    return [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a))) for a in (90, 210, 330)]


# ---------------------------------------------------------------- bought hardware (stand-ins)
def hardware(p) -> dict:
    """Named stand-ins of the bought parts in the closed position; not printed."""
    h = heart.hinge(p)
    lv = levels(p)
    out = {}
    for name, side in heart.SIDES.items():
        f = h.frame
        out[f"hinge_pin_{name}"] = _mirror(
            rod(f, p.pin_d / 2, shell.pin_bottom(p), shell.pin_top(p, h)), side
        )
    follower = kin.slider_y(p, 0.0) + kin.follower_offset(p)
    tip = lv.cam_top - p.groove_depth + 0.3
    out["follower_pin"] = Pos(0, follower, 0) * rod(Plane.XY, p.follower_d / 2, tip, tip + 12.0)
    out["ballast_washer"] = rod(Plane.XY, WASHER_OD / 2, lv.washer_bottom, lv.washer_top) - rod(
        Plane.XY, WASHER_ID / 2, lv.washer_bottom - 1, lv.washer_top + 1
    )
    head = lv.foot_bottom + 0.3
    screw = rod(Plane.XY, 2.0, head, head + M4_HEAD_H + 12.0) + rod(
        Plane.XY, M4_HEAD_D / 2, head, head + M4_HEAD_H
    )
    out["tie_screw"] = screw
    nut = hex_prism(M4_NUT_AF / math.sqrt(3), M4_NUT_H) - Cylinder(2.0, M4_NUT_H + 1)
    out["tie_nut"] = Pos(0, 0, lv.slider_bottom - 0.1 - M4_NUT_H / 2) * nut
    seat = back_screw_seat(p)
    for i, y in enumerate(BACK_SCREWS_Y):
        out[f"back_screw_{i}"] = Pos(0, y, 0) * (
            rod(Plane.XY, 1.5, seat, seat + 8.0)
            + rod(Plane.XY, M3_HEAD_D / 2, seat - M3_HEAD_H, seat)
        )
        out[f"back_insert_{i}"] = Pos(0, y, 0) * (
            rod(Plane.XY, INSERT_D / 2, ridge_z(p), ridge_z(p) + INSERT_LEN)
            - rod(Plane.XY, 1.5, ridge_z(p) - 1, ridge_z(p) + INSERT_LEN + 1)
        )
    for i, sx in enumerate((-1, 1)):
        x = sx * (LEG_X + LEG_W / 2)
        z = lv.chassis_bottom
        out[f"leg_screw_{i}"] = Pos(x, 0, 0) * rod(Plane.XY, 1.5, z, z + 6.0) + Pos(
            x, 0, z + 0.85
        ) * Cone(M3_HEAD_D / 2 - 0.05, 1.5, 1.7)
        out[f"leg_insert_{i}"] = Pos(x, 0, 0) * (
            rod(Plane.XY, INSERT_D / 2, lv.slider_bottom, lv.slider_bottom + INSERT_LEN)
            - rod(Plane.XY, 1.5, lv.slider_bottom - 1, lv.slider_bottom + INSERT_LEN + 1)
        )
    for i, (x, y) in enumerate(magnet_positions()):
        out[f"cam_magnet_{i}"] = Pos(x, y, 0) * rod(
            Plane.XY, MAGNET_D / 2, lv.cam_bottom, lv.cam_bottom + MAGNET_H
        )
        out[f"ring_magnet_{i}"] = Pos(x, y, 0) * rod(
            Plane.XY, MAGNET_D / 2, lv.web_top - MAGNET_H, lv.web_top
        )
    for i, (x, y) in enumerate(feet_positions(p)):
        out[f"foot_pad_{i}"] = Pos(x, y, 0) * rod(
            Plane.XY, FOOT_D / 2, lv.foot_bottom + 0.3 - FOOT_H, lv.foot_bottom + 0.3
        )
    return out


def total_height(p) -> float:
    """From the table to the top of the heart is this plus the heart's top z."""
    return -(levels(p).foot_bottom + 0.3 - FOOT_H)


def back_insert_pockets(p) -> list:
    """Pockets in the cellar of the back half for the inserts of the two back screws."""
    z = ridge_z(p)
    return [
        Pos(0, y, 0) * rod(Plane.XY, INSERT_D / 2, z - 2.5, z + INSERT_LEN + 0.6)
        for y in BACK_SCREWS_Y
    ]
