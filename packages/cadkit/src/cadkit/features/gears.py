"""Involute spur gears for printed drives: profile, solid and the angle at which a pair meshes.

Standard 20 degree full-depth teeth (ISO 53 basic rack: addendum 1 module, dedendum 1.25
modules). `shift` is the profile shift coefficient: a small pinion takes a positive shift to
avoid undercut and its mate the same negative shift, which keeps the standard centre distance.
`backlash` thins every tooth by that amount along the pitch circle, as running clearance for a
printed pair. The flank below the base circle is a radial line, without the trochoid a cutter
would leave; a pair must therefore be checked for interference, which `overlaps` does.

Lengths in mm, angles in degrees.
"""

import math

from build123d import Cylinder, Polyline, Solid, extrude, make_face

PRESSURE_ANGLE = 20.0


def _involute(angle: float) -> float:
    return math.tan(angle) - angle


def pitch_radius(module: float, teeth: int) -> float:
    """Radius of the pitch circle."""
    return module * teeth / 2


def centre_distance(module: float, teeth_a: int, teeth_b: int) -> float:
    """Shaft spacing of a pair whose profile shifts cancel."""
    return module * (teeth_a + teeth_b) / 2


def gear_outline(
    module: float, teeth: int, shift: float = 0.0, backlash: float = 0.0, steps: int = 7
) -> list[tuple[float, float]]:
    """Closed outline of the gear in its own plane; a tooth is centred on the +X axis."""
    if module <= 0 or teeth < 6 or steps < 3:
        raise ValueError("Require a positive module, at least 6 teeth and 3 flank steps")
    alpha = math.radians(PRESSURE_ANGLE)
    pitch = pitch_radius(module, teeth)
    base = pitch * math.cos(alpha)
    tip = pitch + module * (1 + shift)
    root = pitch - module * (1.25 - shift)
    thickness = module * (math.pi / 2 + 2 * shift * math.tan(alpha)) - backlash
    if thickness <= 0 or root <= 0:
        raise ValueError("Tooth vanishes: reduce the backlash or the negative shift")

    def half_angle(r):  # half the tooth's angular width at radius r
        return thickness / (2 * pitch) + _involute(alpha) - _involute(math.acos(base / r))

    start = max(base, root)
    radii = [start + (tip - start) * i / (steps - 1) for i in range(steps)]
    while half_angle(radii[-1]) <= 0:  # a pointed tooth: stop where the flanks meet
        radii.pop()
        if len(radii) < 2:
            raise ValueError("Tooth is pointed below its base: reduce the positive shift")
    flank = [(r, half_angle(r)) for r in radii]
    if root < base:
        flank.insert(0, (root, flank[0][1]))
    step = math.tau / teeth
    points = []
    for i in range(teeth):
        centre = i * step
        for r, a in flank:  # rising flank, on the clockwise side of the tooth
            points.append((r * math.cos(centre - a), r * math.sin(centre - a)))
        for r, a in reversed(flank):
            points.append((r * math.cos(centre + a), r * math.sin(centre + a)))
    return points


def spur_gear(
    module: float,
    teeth: int,
    width: float,
    shift: float = 0.0,
    backlash: float = 0.0,
    bore: float = 0.0,
) -> Solid:
    """Gear about the Z axis from z = 0 to `width`; a tooth is centred on the +X axis."""
    if width <= 0 or bore < 0:
        raise ValueError("Require a positive width and a bore that is not negative")
    outline = gear_outline(module, teeth, shift, backlash)
    gear = extrude(make_face(Polyline(*outline, close=True)), amount=width)
    if bore:
        gear -= Cylinder(bore / 2, 3 * width)
    return gear


def meshing_angle(teeth_a: int, teeth_b: int, angle_a: float, towards: float = 0.0) -> float:
    """Turn of gear B that meshes with gear A turned by `angle_a`.

    Both gears are built with a tooth on their own +X axis; B lies in the direction `towards`
    (degrees, in the gears' plane) from A. External gears turn in opposite senses.
    """
    return towards + 180.0 + 180.0 / teeth_b - (angle_a - towards) * teeth_a / teeth_b
