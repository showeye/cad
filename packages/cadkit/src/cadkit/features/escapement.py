"""Recoil anchor escapement for printed clockwork: escape wheel, pallets and how they meet.

The escape wheel has pointed teeth and turns clockwise, seen with X to the right and Y up.
The anchor rocks on a pivot straight above the wheel and reaches round `span + 1/2` tooth
pitches. Its two pallets stand where the lines from the pivot touch the wheel's tip circle,
so a pallet moves straight in and out of the wheel when the anchor rocks. A pallet's working
face is a ramp: a tooth pushing along it wedges the pallet out of the wheel, which pushes the
other pallet in. When the tooth leaves the ramp's inner end the wheel is free for `drop`,
until another tooth lands on the other pallet. One tooth passes for every two such beats.
If the anchor swings on past `release`, the ramp pushes the wheel back: that is the recoil.

The released tooth must not be caught by the pallet that falls in behind it, and a pallet's
nose must find room between two teeth: both flanks of a tooth and the back of a pallet are
therefore steeper than the ramp. `interference` checks the tooth tips at any position; the
flanks have to be checked on the solids.

For a wheel that turns the other way, mirror every outline. Lengths in mm, angles in degrees;
the anchor's angle is counter-clockwise, so a positive angle lowers the entry pallet, which is
the left one. Rigid geometry only: no friction, no dynamics.
"""

import math
from dataclasses import dataclass

Point = tuple[float, float]


def _unit(angle: float) -> Point:
    return math.cos(math.radians(angle)), math.sin(math.radians(angle))


def _turn(point: Point, angle: float, about: Point = (0.0, 0.0)) -> Point:
    c, s = _unit(angle)
    x, y = point[0] - about[0], point[1] - about[1]
    return about[0] + c * x - s * y, about[1] + s * x + c * y


@dataclass(frozen=True)
class RecoilEscapement:
    """A recoil anchor escapement; the wheel's centre is the origin, its pivot at +Y.

    `release` is the anchor's angle either side of centre at which a tooth leaves a pallet;
    the pendulum has to swing further than that. `drop` is the free travel of a tooth tip
    between leaving one pallet and landing on the other, the allowance for printing error.
    `tooth_angle` is the angle between a tooth's flanks, `land` the flat at its tip, `back`
    the angle of a pallet's back face from the wheel's tangent.
    """

    teeth: int
    tip_radius: float
    span: int
    release: float
    drop: float
    tooth_angle: float = 36.0
    land: float = 0.3
    back: float = 75.0

    def __post_init__(self):
        if self.teeth < 8 or self.tip_radius <= 0 or not 1 <= self.span < self.teeth / 4:
            raise ValueError("Require at least 8 teeth and an anchor that spans under 90 degrees")
        if self.release <= 0 or self.drop <= 0 or self.impulse <= 0:
            raise ValueError("Release and drop must be positive and leave travel on a pallet")
        if not self.ramp + 5 <= min(self.back, 90 - self.tooth_angle / 2):
            raise ValueError("Ramp is too steep for the teeth or the pallets: reduce the release")

    @property
    def pitch(self) -> float:
        """Angle from tooth to tooth."""
        return 360 / self.teeth

    @property
    def half_span(self) -> float:
        """Angle at the wheel's centre between the pivot and either pallet."""
        return (self.span + 0.5) * self.pitch / 2

    @property
    def pivot_distance(self) -> float:
        """From the wheel's centre to the anchor's pivot."""
        return self.tip_radius / math.cos(math.radians(self.half_span))

    @property
    def lever(self) -> float:
        """From the pivot to a pallet."""
        return self.tip_radius * math.tan(math.radians(self.half_span))

    @property
    def engagement(self) -> float:
        """How far a pallet's corner stands inside the tip circle with the anchor centred."""
        return self.lever * math.radians(self.release)

    @property
    def impulse(self) -> float:
        """Travel of a tooth tip along a pallet, from landing to leaving, anchor permitting."""
        return self.tip_radius * math.radians(self.pitch) / 2 - self.drop

    @property
    def ramp(self) -> float:
        """Angle of a pallet's working face from the wheel's tangent."""
        return math.degrees(math.atan2(2 * self.engagement, self.impulse))

    @property
    def pivot(self) -> Point:
        return 0.0, self.pivot_distance

    def beats(self, turn: float) -> float:
        """Number of beats while the wheel turns by `turn` degrees."""
        return 2 * turn / self.pitch

    # ------------------------------------------------------------ outlines
    def wheel_outline(self, depth: float, progress: float = 0.0) -> list[Point]:
        """Closed outline of the escape wheel with teeth `depth` deep.

        `progress` is the wheel's clockwise turn from the position in which a tooth is just
        leaving the entry pallet of an anchor standing at -release.
        """
        half = math.radians(self.tooth_angle / 2)
        root = self.tip_radius - depth
        foot = self.land / 2 + depth * math.tan(half)  # half width of a tooth at its root
        if depth <= 0 or root <= 0 or 2 * foot >= root * math.radians(self.pitch):
            raise ValueError("Teeth would overlap at the root: reduce the depth or tooth angle")
        points = []
        for i in range(self.teeth):
            centre = self._tooth(i, progress)
            for x, y in (
                (-foot, root),
                (-self.land / 2, self.tip_radius),
                (self.land / 2, self.tip_radius),
                (foot, root),
            ):
                # drawn pointing +Y, then turned to its place; counter-clockwise order
                points.append(_turn((-x, y), centre - 90))
        return points

    def pallets(self, length: float) -> tuple[list[Point], list[Point]]:
        """The entry and exit pallet with the anchor centred: [corner, back, ramp end].

        `length` is that of the ramp and of the back face. Each is the nose of a pallet; the
        anchor's arms join them to the pivot and must stay outside the tip circle.
        """
        if length <= 0:
            raise ValueError("Pallet faces need a positive length")
        ramp, back = math.radians(self.ramp), math.radians(self.back)
        noses = []
        for side in (1, -1):
            at = 90 + side * self.half_span
            out, along = _unit(at), _unit(at - 90)  # along: the way a tooth travels
            reach = self.tip_radius - self.engagement
            corner = (reach * out[0], reach * out[1])
            noses.append(
                [
                    corner,
                    (
                        corner[0] + length * (math.cos(back) * along[0] + math.sin(back) * out[0]),
                        corner[1] + length * (math.cos(back) * along[1] + math.sin(back) * out[1]),
                    ),
                    (
                        corner[0] + length * (math.sin(ramp) * out[0] - math.cos(ramp) * along[0]),
                        corner[1] + length * (math.sin(ramp) * out[1] - math.cos(ramp) * along[1]),
                    ),
                ]
            )
        return noses[0], noses[1]

    # ------------------------------------------------------------ how they meet
    def _tooth(self, index: int, progress: float) -> float:
        """Direction of a tooth's centre line."""
        lead = math.degrees(self.land / 2 / self.tip_radius)
        return 90 + self.half_span + lead - progress + index * self.pitch

    def tips(self, progress: float) -> list[Point]:
        """Both corners of every tooth's land for a wheel turned clockwise by `progress`."""
        lead = math.degrees(self.land / 2 / self.tip_radius)
        found = []
        for i in range(self.teeth):
            centre = self._tooth(i, progress)
            for corner in (centre - lead, centre + lead):
                x, y = _unit(corner)
                found.append((self.tip_radius * x, self.tip_radius * y))
        return found

    def interference(self, progress: float, angle: float, length: float = 5.0) -> float:
        """Deepest reach of a tooth tip into a pallet; zero when the tips are clear.

        Wheel turned clockwise by `progress`, anchor turned counter-clockwise by `angle`.
        """
        deepest = 0.0
        tips = self.tips(progress)
        for nose in self.pallets(length):
            placed = [_turn(p, angle, self.pivot) for p in nose]
            area = sum(a[0] * b[1] - a[1] * b[0] for a, b in zip(placed, placed[1:] + placed[:1]))
            if area < 0:
                placed.reverse()
            edges = list(zip(placed, placed[1:] + placed[:1]))
            for x, y in tips:
                inside = min(
                    ((b[0] - a[0]) * (y - a[1]) - (b[1] - a[1]) * (x - a[0])) / math.dist(a, b)
                    for a, b in edges
                )
                deepest = max(deepest, inside)
        return deepest

    def settle(self, progress: float, angle: float, length: float = 5.0) -> float:
        """Where a wheel that is pushed on from `progress` comes to rest against a pallet.

        If a pallet already stands in a tooth at `progress`, the wheel is pushed back to where
        it is clear: the recoil. Returns at most one pitch beyond `progress` if nothing stops
        the wheel. The search steps by 1/400 of a pitch, so a pallet that stands less than
        that inside the tip circle, within about 0.1 degree of its release, may be passed.
        """
        step = self.pitch / 400

        def clear(at):
            return self.interference(at, angle, length) <= 1e-9

        if clear(progress):
            low = progress
            while clear(low + step):
                low += step
                if low - progress >= self.pitch:
                    return progress + self.pitch
            high = low + step
        else:
            high = progress
            while not clear(high - step):
                high -= step
                if progress - high >= self.pitch:
                    raise ValueError("Anchor stands too deep in the wheel to be cleared")
            low = high - step
        for _ in range(30):
            middle = (low + high) / 2
            low, high = (middle, high) if clear(middle) else (low, middle)
        return low
