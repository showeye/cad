"""Involute spur gears and racks for printed drives: profile, solid and how a pair meshes.

Standard 20 degree full-depth teeth (ISO 53 basic rack: addendum 1 module, dedendum 1.25
modules). `shift` is the profile shift coefficient: a small pinion takes a positive shift to
avoid undercut and its mate the same negative shift, which keeps the standard centre distance.
`backlash` thins every tooth by that amount along the pitch circle, as running clearance for a
printed pair. The flank below the base circle is a radial line, without the trochoid a cutter
would leave; a pair must therefore be checked for interference, which `overlaps` does.

A rack is the same basic rack as a solid: straight flanks at the pressure angle. It takes the
profile shift of its mate, so the mate's pitch circle always rolls on the line x = 0.

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


def rack_outline(
    module: float, teeth: int, depth: float, shift: float = 0.0, backlash: float = 0.0
) -> list[tuple[float, float]]:
    """Closed outline of a straight rack along Y whose teeth point +X.

    The mate's pitch circle rolls on the line x = 0: its axis stands at x = pitch radius,
    whatever its profile shift, which is passed here as `shift` and sets the teeth back by
    shift * module. Teeth are centred on y = (k + 1/2) * pi * module for k = 0 .. teeth - 1,
    so a tooth space is centred on y = 0 and the outline ends in the middle of a space at both
    ends. `depth` is the solid body behind the root line.
    """
    if module <= 0 or teeth < 1 or depth <= 0:
        raise ValueError("Require a positive module and depth and at least one tooth")
    tangent = math.tan(math.radians(PRESSURE_ANGLE))
    pitch = math.pi * module
    reference = -shift * module  # where a tooth is as thick as a space, less the backlash
    tip, root = reference + module, reference - 1.25 * module
    at_tip = pitch / 4 - backlash / 2 - module * tangent  # half thickness at the tip
    at_root = pitch / 4 - backlash / 2 + 1.25 * module * tangent
    if at_tip <= 0 or at_root >= pitch / 2:
        raise ValueError("Tooth vanishes: reduce the backlash")
    points = [(root - depth, 0.0), (root, 0.0)]
    for k in range(teeth):
        centre = (k + 0.5) * pitch
        points += [
            (root, centre - at_root),
            (tip, centre - at_tip),
            (tip, centre + at_tip),
            (root, centre + at_root),
        ]
    return points + [(root, teeth * pitch), (root - depth, teeth * pitch)]


def rack(
    module: float,
    teeth: int,
    width: float,
    depth: float,
    shift: float = 0.0,
    backlash: float = 0.0,
) -> Solid:
    """Rack along Y from z = 0 to `width`, teeth pointing +X; see `rack_outline`."""
    if width <= 0:
        raise ValueError("Require a positive width")
    outline = rack_outline(module, teeth, depth, shift, backlash)
    return extrude(make_face(Polyline(*outline, close=True)), amount=width)


def rack_offset(module: float, teeth: int, angle: float) -> float:
    """Shift along Y, within one pitch, at which a rack meshes with a gear turned by `angle`.

    The gear has `teeth` teeth, is built with a tooth on its own +X axis and stands on the
    rack's +X side with its axis at (pitch radius, 0). Turning the gear counter-clockwise
    moves the rack towards -Y by the pitch radius times the angle.
    """
    pitch = math.pi * module
    return pitch_radius(module, teeth) * (math.pi - math.radians(angle)) % pitch
