"""Szyb Prezydent, Chorzów (1933): scale model of the reinforced-concrete headframe.

Axes: X runs from the shaft towards the strut feet (the winding-engine side, west on site),
Y across, Z up. The origin is the shaft axis at ground level and the tower is symmetric about
the XZ plane. `Prototype` is the real tower in metres, the only place this repository uses
metres; `build` multiplies by 1000 / scale, and everything after that is mm.

Where each figure comes from is in docs/research.md. In `Prototype`, [P] marks a published
figure and [M] one measured from photographs (about +/-5 %); no survey drawing was available.
"""

import math

from build123d import Axis, Box, Color, Cylinder, Pos, Rot, Solid, chamfer, fillet
from cadkit.features.polyhedron import convex_solid
from cadkit.model import Model
from cadkit.params import Params as BaseParams
from cadkit.process import U1
from pydantic import Field

_LAP = 0.2  # mm by which stacked members overlap, so that they fuse through a volume


class Prototype(BaseParams):
    """The real tower, full size, in metres."""

    # Trunk: four corner posts, tied by beams on all four faces at every level.
    trunk_x: float = 5.8  # [M] outer plan size along X
    trunk_y: float = 5.1  # [M] outer plan size along Y
    post_x: float = 0.65  # [M]
    post_y: float = 0.6  # [M]
    post_foot_x: float = 0.9  # [M] shaft-side posts at the ground
    taper_z: float = 9.3  # [M] below this level the posts and piers taper to the ground
    beam_levels: tuple[float, ...] = (2.25, 5.9, 9.55, 12.5, 16.1, 19.2, 23.05, 26.1, 29.1, 31.8)
    portal_levels: int = 2  # [M] the strut-side face is open below: no beam at these levels
    beam_depth: float = 0.5  # [M]
    beam_width: float = 0.4  # estimated: never seen square-on
    # Piers: the strut-side posts are walls up to the brace frame, narrower at the ground.
    pier_x: float = 2.2  # [M]
    pier_y: float = 1.1  # [M]
    pier_out: float = 0.3  # [M] how far a pier stands proud of the trunk face
    pier_foot_x: float = 1.2  # [M]
    pier_foot_shift: float = 0.375  # [M] its shaft-side edge moves this far out at the ground
    # Brace frame: a beam from each strut to its pier, and a cross beam between the struts.
    brace_top: float = 19.2  # [M]
    brace_depth: float = 1.7  # [M]
    cross_depth: float = 1.5  # [M]
    brace_width: float = 0.9  # [M]
    haunch: float = 1.0  # [M] 45 degree haunches at the piers and under the cross beam
    haunch_strut: tuple[float, float] = (1.9, 1.1)  # [M] run and drop where a beam meets a strut
    # Head: viewing terrace, the box that carries the sheave deck, the hood over the rope window.
    terrace_z: tuple[float, float] = (34.05, 34.95)  # floor at 34 m [P]; the edge beam is [M]
    terrace_reach: float = 3.2  # [M] beyond the trunk, towards the struts
    box_z: float = 37.8  # [M] underside of the box walls
    deck_z: float = 42.0  # [P] the platform that carries the sheaves
    slab_depth: float = 1.0  # [M] edge of the deck slab
    slab_over: float = 0.15  # [M] its overhang beyond the walls
    head_reach: float = 4.3  # [M] box beyond the trunk, towards the struts
    hood_run: float = 1.0  # [M]
    hood_z: tuple[float, float] = (36.6, 38.1)  # [M]
    hood_depth: float = 0.6  # estimated
    # Struts: one on each side, leaning in both directions; they end inside the box.
    foot_x: float = 21.0  # [P] footing to the tower axis
    foot_spread: float = 15.0  # [P] between the two struts at the ground
    strut_top_x: float = 3.1  # [M] where the axis would cross deck level
    strut_top_y: float = 1.23  # [M] the same, across
    strut_depth: float = 1.45  # [M] square to the axis, in the plane of the lean
    strut_width: tuple[float, float] = (2.0, 1.33)  # [M] across, at the ground and at deck level
    footing_x: tuple[float, float] = (-1.0, 3.0)  # [M] base along X, from the strut foot
    footing_y: float = 5.0  # [M]
    footing_top_x: tuple[float, float] = (-0.9, 0.7)  # [M]
    footing_top_y: float = 2.6  # [M]
    footing_z: float = 1.3  # [M]
    # Rope sheaves: 5.5 m [P] is the rope tread; the rim measures about 5.8 m across [M].
    sheave_d: float = 5.8
    sheave_gap: float = 2.1  # [P] "over 2 m" between the two; 2.09 [M]
    sheave_x: float = 3.6  # [M] axle, from the tower axis
    sheave_lift: float = 0.5  # [M] axle above the deck
    sheave_thick: float = 0.33  # [M]
    sheave_rim: float = 0.22  # estimated
    sheave_spoke: float = 0.12  # estimated
    sheave_axle: float = 0.3  # estimated
    slot: tuple[float, float, float] = (6.1, 0.65, 2.6)  # [M] length, width; depth is a choice


class Params(BaseParams):
    """One printed edition: its scale and the floors that printing puts under thin members."""

    scale: float = Field(default=250, ge=180, le=400)  # the model is 1 : scale
    feature: float = Field(default=1.6, ge=1.2, le=2.4)  # thinnest printed member
    clearance: float = Field(default=0.5, ge=0.3, le=1.0)  # around a sheave in its slot
    base: float = Field(default=3.0, ge=2, le=6)  # plinth thickness
    margin: float = Field(default=6.0, ge=4, le=20)  # plinth beyond the footprint
    tower: Prototype = Prototype()


def _printed(p: Params, member: str) -> float:
    """Printed size of a named `Prototype` member: true to scale, or the floor if that is more."""
    floor = p.feature * (0.75 if member == "sheave_spoke" else 1)
    return max(getattr(p.tower, member) * 1000 / p.scale, floor)


_MEMBERS = (
    ("concrete", "post, thinner side", "post_y"),
    ("concrete", "tie beam, depth", "beam_depth"),
    ("concrete", "tie beam, width", "beam_width"),
    ("concrete", "brace beam, width", "brace_width"),
    ("concrete", "strut, depth", "strut_depth"),
    ("concrete", "hood slab", "hood_depth"),
    ("fittings", "sheave, thickness", "sheave_thick"),
    ("fittings", "sheave, rim", "sheave_rim"),
    ("fittings", "sheave, spoke", "sheave_spoke"),
    ("fittings", "sheave, axle", "sheave_axle"),
)


def fidelity(p: Params) -> list[dict]:
    """What printing does to the thin members: real size in m, true-to-scale and printed mm."""
    return [
        {
            "group": group,
            "member": label,
            "real": getattr(p.tower, name),
            "true": round(getattr(p.tower, name) * 1000 / p.scale, 3),
            "printed": round(_printed(p, name), 3),
        }
        for group, label, name in _MEMBERS
    ]


def _block(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def _frustum(*levels):
    """Convex solid through axis-aligned rectangles, each given as (x0, x1, y0, y1, z)."""
    return convex_solid([(x, y, r[4]) for r in levels for x in r[:2] for y in r[2:4]])


def _beam(a, b, width, z0, z1):
    """Level beam between the plan points a and b."""
    length = math.dist(a, b)
    nx, ny = (a[1] - b[1]) / length * width / 2, (b[0] - a[0]) / length * width / 2
    plan = [(q[0] + s * nx, q[1] + s * ny) for q in (a, b) for s in (1, -1)]
    return convex_solid([(x, y, z) for x, y in plan for z in (z0, z1)])


def _haunch(at, towards, run, drop, width, z):
    """Triangular haunch under a soffit at z: its full drop at `at`, nothing after `run`."""
    length = math.dist(at, towards)
    ux, uy = (towards[0] - at[0]) / length, (towards[1] - at[1]) / length
    end = (at[0] + ux * run, at[1] + uy * run)
    points = []
    for s in (1, -1):
        nx, ny = -uy * s * width / 2, ux * s * width / 2
        points += [
            (at[0] + nx, at[1] + ny, z),
            (at[0] + nx, at[1] + ny, z - drop),
            (end[0] + nx, end[1] + ny, z),
        ]
    return convex_solid(points)


def _concrete(p: Params):
    """Everything cast in 1933, as one solid standing on z = 0."""
    t, k = p.tower, 1000 / p.scale
    hx, hy = t.trunk_x * k / 2, t.trunk_y * k / 2
    px, py = t.post_x * k, t.post_y * k
    deck, taper, brace = t.deck_z * k, t.taper_z * k, t.brace_top * k
    slab = deck - t.slab_depth * k
    solids = []

    # Trunk posts and piers.
    inner = hx - px
    pier_x1, foot0 = inner + t.pier_x * k, inner + t.pier_foot_shift * k
    for s in (1, -1):
        y0, y1 = sorted((s * (hy - py), s * hy))
        q0, q1 = sorted((s * (hy + (t.pier_out - t.pier_y) * k), s * (hy + t.pier_out * k)))
        solids += [
            _frustum((-hx, -hx + t.post_foot_x * k, y0, y1, 0), (-hx, -hx + px, y0, y1, taper)),
            _block(-hx, -hx + px, y0, y1, taper - _LAP, deck - _LAP),
            _block(inner, hx, y0, y1, brace - _LAP, deck - _LAP),
            _frustum(
                (foot0, foot0 + t.pier_foot_x * k, q0, q1, 0),
                (inner, pier_x1, q0, q1, taper),
                (inner, pier_x1, q0, q1, brace),
            ),
        ]

    # Tie beams, on the post centre lines.
    bw, bd = _printed(p, "beam_width"), _printed(p, "beam_depth")
    cx, cy = hx - px / 2, hy - py / 2
    for i, level in enumerate(t.beam_levels):
        z0, z1 = level * k - bd / 2, level * k + bd / 2
        for s in (1, -1):
            solids.append(_block(-cx, cx, s * cy - bw / 2, s * cy + bw / 2, z0, z1))
            if s < 0 or i >= t.portal_levels:
                solids.append(_block(s * cx - bw / 2, s * cx + bw / 2, -cy, cy, z0, z1))

    # Head: terrace, box, deck slab and the hood under the far end of the box.
    reach, over = hx + t.head_reach * k, t.slab_over * k
    hood0, hood1 = t.hood_z[0] * k, t.hood_z[1] * k
    nose = reach - t.hood_run * k
    solids += [
        _block(-hx, hx + t.terrace_reach * k, -hy, hy, t.terrace_z[0] * k, t.terrace_z[1] * k),
        _block(-hx, reach, -hy, hy, t.box_z * k, slab + _LAP),
        _block(-hx - over, reach + over, -hy - over, hy + over, slab, deck),
        convex_solid(
            [
                (x, y, z)
                for x, z in (
                    (reach, hood1),
                    (nose, hood0),
                    (nose - _printed(p, "hood_depth"), hood0),
                    (nose - _printed(p, "hood_depth"), hood1),
                )
                for y in (-hy, hy)
            ]
        ),
    ]

    # Struts and their footings. A strut is described by level sections: at height z its axis
    # is at (x, +/-y) and it is `half` either side of that along X and w / 2 across.
    run = (t.foot_x - t.strut_top_x) / t.deck_z
    half = _printed(p, "strut_depth") / 2 * math.hypot(1, run)

    def strut(z):
        u = z / deck
        return (
            (t.foot_x - (t.foot_x - t.strut_top_x) * u) * k,
            (t.foot_spread / 2 - (t.foot_spread / 2 - t.strut_top_y) * u) * k,
            (t.strut_width[0] + (t.strut_width[1] - t.strut_width[0]) * u) * k,
        )

    def section(z, s, grow=0.0):
        x, y, w = strut(z)
        y0, y1 = sorted((s * (y - w / 2 - grow), s * (y + w / 2 + grow)))
        return (x - half, x + half, y0, y1, z)

    for s in (1, -1):
        fx, fy = t.foot_x * k, s * t.foot_spread * k / 2
        solids += [
            _frustum(section(0, s), section(slab, s)),
            _frustum(
                (
                    fx + t.footing_x[0] * k,
                    fx + t.footing_x[1] * k,
                    fy - t.footing_y * k / 2,
                    fy + t.footing_y * k / 2,
                    0,
                ),
                (
                    fx + t.footing_top_x[0] * k,
                    fx + t.footing_top_x[1] * k,
                    fy - t.footing_top_y * k / 2,
                    fy + t.footing_top_y * k / 2,
                    t.footing_z * k,
                ),
            ),
        ]

    # Brace frame. The cross beam lies in the plane of the struts; the two side beams are level.
    wide = _printed(p, "brace_width")
    side0, cross0 = brace - t.brace_depth * k, brace - t.cross_depth * k
    hb = wide / 2 * math.hypot(1, run)
    lower, upper = strut(cross0), strut(brace)
    solids.append(
        _frustum(
            (lower[0] - hb, lower[0] + hb, -lower[1], lower[1], cross0),
            (upper[0] - hb, upper[0] + hb, -upper[1], upper[1], brace),
        )
    )
    drop = t.haunch * k
    under = strut(cross0 - drop)
    sx, sy, _ = strut((side0 + brace) / 2)
    pier_y = hy + (t.pier_out - t.pier_y / 2) * k
    for s in (1, -1):
        # under the cross beam, in the plane of the struts
        face0, face1 = lower[1] - lower[2] / 2, under[1] - under[2] / 2
        solids.append(
            convex_solid(
                [
                    (x0 + e, s * y, z)
                    for x0, y, z in (
                        (lower[0], face0 + wide / 2, cross0 + _LAP),
                        (lower[0], face0 - drop, cross0 + _LAP),
                        (under[0], face1 + wide / 2, cross0 - drop),
                    )
                    for e in (-hb, hb)
                ]
            )
        )
        # side beam from the strut to the pier, with a haunch at each end
        a, b = (sx, s * sy), (pier_x1 - wide / 2, s * pier_y)
        solids.append(_beam(a, b, wide, side0, brace))
        solids.append(_haunch(b, a, drop + wide / 2, drop + wide / 2, wide, side0 + _LAP))
        fall = t.haunch_strut[1] * k
        leg = strut(side0 - fall)[0] - half / 2  # inside the strut at the foot of the haunch
        part = (a[0] - leg) / (a[0] - b[0])
        at = (leg, a[1] + part * (b[1] - a[1]))
        solids.append(_haunch(at, b, t.haunch_strut[0] * k + half / 2, fall, wide, side0 + _LAP))

    solids = [shape if isinstance(shape, Solid) else shape.solid() for shape in solids]
    body = solids[0].fuse(*solids[1:]).clean()
    return body.cut(*_slots(p, 1)).clean()


def _slots(p: Params, over: float = 0.0):
    """The two openings in the deck that the sheaves hang in, as cutting tools."""
    t, k = p.tower, 1000 / p.scale
    thick, r = _printed(p, "sheave_thick"), t.sheave_d * k / 2
    length = max(t.slot[0] * k, 2 * (r + p.clearance))
    width = max(t.slot[1] * k, thick + 2 * p.clearance)
    depth = max(t.slot[2] * k, r - t.sheave_lift * k + p.clearance)
    x, deck = t.sheave_x * k, t.deck_z * k
    return [
        _block(
            x - length / 2,
            x + length / 2,
            s * t.sheave_gap * k / 2 - width / 2,
            s * t.sheave_gap * k / 2 + width / 2,
            deck - depth,
            deck + over,
        )
        for s in (1, -1)
    ]


def _sheave(p: Params, s: int):
    """Spoked rope sheave on its axle and two bearing pedestals that stand on the deck."""
    t, k = p.tower, 1000 / p.scale
    r, thick = t.sheave_d * k / 2, _printed(p, "sheave_thick")
    rim, spoke = _printed(p, "sheave_rim"), _printed(p, "sheave_spoke")
    axle = _printed(p, "sheave_axle") / 2
    hub = max(2 * axle, 0.45 * k)
    wheel = Cylinder(r, thick) - Cylinder(r - rim, thick + 1) + Cylinder(hub, thick)
    reach = r - rim / 2
    for i in range(8):
        wheel += Rot(0, 0, i * 45) * Pos(reach / 2, 0, 0) * Box(reach, spoke, thick)
    width = max(t.slot[1] * k, thick + 2 * p.clearance)
    pedestal = (max(0.6 * k, 1.5 * p.feature), p.feature)  # along X, along Y
    lift = t.sheave_lift * k
    shape = Rot(90, 0, 0) * (wheel + Cylinder(axle, width + 2 * pedestal[1] - _LAP))
    for side in (1, -1):
        y = side * (width + pedestal[1]) / 2
        shape += Pos(0, y, (axle - lift) / 2) * Box(pedestal[0], pedestal[1], lift + axle)
    return Pos(t.sheave_x * k, s * t.sheave_gap * k / 2, t.deck_z * k + lift) * shape


def _base(p: Params, body):
    """Plain plinth under the whole footprint; its top is the ground, z = 0."""
    box, m = body.bounding_box(), p.margin
    plate = _block(box.min.X - m, box.max.X + m, box.min.Y - m, box.max.Y + m, -p.base, 0)
    plate = fillet(plate.edges().filter_by(Axis.Z), radius=m)
    return chamfer(plate.edges().group_by(Axis.Z)[-1], length=0.6)


def build(p: Params):
    """The four printed parts in assembly position; each is one solid."""
    body = _concrete(p)
    parts = {
        "concrete": (body, Color(0.80, 0.79, 0.76)),
        "sheave_1": (_sheave(p, 1), Color(0.72, 0.08, 0.12)),
        "sheave_2": (_sheave(p, -1), Color(0.72, 0.08, 0.12)),
        "base": (_base(p, body), Color(0.13, 0.13, 0.14)),
    }
    for name, (shape, colour) in parts.items():
        shape.label, shape.color = name, colour
    return {name: shape for name, (shape, _) in parts.items()}


presentation = {
    "sheet": {
        "title": "SZYB PREZYDENT",
        "subtitle": "{name}  /  1:250  /  {version}  /  CAD study, not yet printed",
        "caption": "Chorzów, 1933 / reinforced-concrete headframe / two 5.5 m rope sheaves",
        "footer": "185 mm tall with its 120 x 92 mm plinth  |  concrete grey, signal red, anthracite",
    },
    # Azimuth 0 looks along +Y; +Y is south on site and +X west, towards the engine house.
    "views": {
        "hero": {"azimuth": 215, "elevation": 14, "size": (1200, 1600)},
        "south": {"azimuth": 201, "elevation": 0, "size": (1200, 1600)},
        "west": {"azimuth": 90, "elevation": 0, "size": (1200, 1600)},
        "head": {
            "azimuth": 205,
            "elevation": 18,
            "size": (1600, 1200),
            "box": ((-16, -14, 128), (34, 14, 184)),
        },
        "top": {"azimuth": 180, "elevation": 89.9, "size": (1600, 1200)},
    },
}

variants = {"s250": Params()}
process = U1
version = "0.1.0"
model = Model("prezydent", version, variants, process, build)
