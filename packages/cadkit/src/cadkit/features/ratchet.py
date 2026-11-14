"""Ratchet wheel with saw teeth, and how a pawl in compression meets it.

A ratchet turns one way only. Each tooth has a steep face, which a pawl pushes or holds, and
a long sloping back, over which a pawl rides when the wheel turns on. Here the wheel turns
counter-clockwise ("forward"), so a tooth's steep face is its clockwise side. The face is
undercut by `rake`: its foot stands ahead of its top, which draws a loaded pawl towards the
root. Each tip carries a small flat (`land`), because a printed point rounds off.

A pawl is a rigid arm on a pivot with a round nose; only the nose is looked at here, as a
circle, so the arm may have any shape that stays clear of the teeth. The pawl works in
compression: seen from the wheel's centre its nose stands counter-clockwise of its pivot. A
pawl on a fixed pivot holds the wheel (a click); one whose pivot is moved drives it.

Lengths in mm, angles in degrees and counter-clockwise, in the wheel's plane with the wheel's
centre at the origin. Rigid geometry only: no friction, no dynamics. Clock ratchets follow no
standard profile; the default rake is common workshop practice, not a normative value.
"""

import math
from dataclasses import dataclass
from functools import cached_property

import numpy as np

Point = tuple[float, float]


def _polar(radius: float, angle: float) -> Point:
    return radius * math.cos(math.radians(angle)), radius * math.sin(math.radians(angle))


def _turn(point: Point, angle: float) -> Point:
    c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    return c * point[0] - s * point[1], s * point[0] + c * point[1]


def _unit(a: Point, b: Point) -> Point:
    length = math.dist(a, b)
    return (b[0] - a[0]) / length, (b[1] - a[1]) / length


@dataclass(frozen=True)
class Pawl:
    """A rigid arm on a pivot: `length` from the pivot to the centre of a nose of radius `nose`."""

    length: float
    nose: float

    def tip(self, pivot: Point, angle: float) -> Point:
        """Centre of the nose with the arm pointing in direction `angle` from the pivot."""
        x, y = _polar(self.length, angle)
        return pivot[0] + x, pivot[1] + y


@dataclass(frozen=True)
class Ratchet:
    """A ratchet wheel that turns counter-clockwise; one tooth's face tops out at 0 degrees.

    `tip` is the radius over the teeth, `depth` the height of a tooth, `rake` the undercut of
    the steep face from the radius through its top, `land` the flat on each tip.
    """

    teeth: int
    tip: float
    depth: float
    rake: float = 8.0
    land: float = 0.3

    def __post_init__(self):
        if self.teeth < 6 or not 0 < self.depth < self.tip / 2:
            raise ValueError("Require at least 6 teeth, lower than half the wheel's radius")
        if not 0 <= self.rake <= 20:
            raise ValueError("Require a rake of 0 to 20 degrees")
        foot = self._tooth[0]
        ahead = math.degrees(math.atan2(foot[1], foot[0]))  # the foot stands ahead of the top
        back = self.pitch + ahead - math.degrees(self.land / self.tip)
        if self.land < 0 or back * math.pi / 180 * self.tip < self.depth:
            raise ValueError("Require a back that is longer than the tooth is high")

    @property
    def pitch(self) -> float:
        """Angle from tooth to tooth."""
        return 360 / self.teeth

    @cached_property
    def _tooth(self) -> tuple[Point, Point, Point]:
        """Foot of the face, its top and the end of the land, for the tooth at 0 degrees."""
        c, s = math.cos(math.radians(self.rake)), math.sin(math.radians(self.rake))
        reach = self.tip * c
        face = reach - math.sqrt(reach**2 - (2 * self.tip - self.depth) * self.depth)
        foot = (self.tip - face * c, face * s)
        return foot, (self.tip, 0.0), _polar(self.tip, math.degrees(self.land / self.tip))

    def outline(self, turn: float = 0.0) -> list[Point]:
        """Closed outline of the wheel turned by `turn`: foot, top and land's end of each tooth."""
        return [
            _turn(point, turn + index * self.pitch)
            for index in range(self.teeth)
            for point in self._tooth
        ]

    @cached_property
    def _edges(self) -> tuple[np.ndarray, np.ndarray]:
        points = np.array(self.outline())
        return points, np.roll(points, -1, axis=0)

    def clearance(self, points, nose: float = 0.0, turn: float = 0.0):
        """Gap between the wheel turned by `turn` and circles of radius `nose` about `points`.

        Negative where a circle overlaps the wheel. `points` is one (x, y) or an array of them;
        the result is a float or an array accordingly.
        """
        given = np.asarray(points, dtype=float)
        c, s = math.cos(math.radians(-turn)), math.sin(math.radians(-turn))
        p = np.atleast_2d(given) @ np.array([[c, s], [-s, c]])  # into the wheel's own frame
        a, b = self._edges
        along = b - a
        offset = p[:, None, :] - a[None, :, :]
        t = np.clip((offset * along).sum(-1) / (along * along).sum(-1), 0.0, 1.0)
        distance = np.linalg.norm(offset - t[..., None] * along, axis=-1).min(axis=1)
        # even-odd rule: a ray towards +X from each point crosses the outline
        px, py = p[:, 0, None], p[:, 1, None]
        spans = (a[:, 1] > py) != (b[:, 1] > py)
        rise = np.where(spans, b[:, 1] - a[:, 1], 1.0)
        crossing = a[:, 0] + (py - a[:, 1]) * along[:, 0] / rise
        inside = (spans & (px < crossing)).sum(axis=1) % 2 == 1
        gap = np.where(inside, -distance, distance) - nose
        return float(gap[0]) if given.ndim == 1 else gap

    def seat(self, nose: float) -> Point:
        """Centre of a round nose lying in the corner below the face of the tooth at 0 degrees.

        The nose touches that face and the back of the tooth behind it. In the wheel's frame.
        """
        foot, top, _ = self._tooth
        behind = _turn(self._tooth[2], -self.pitch)  # where the back of the tooth behind begins
        face, back = _unit(foot, top), _unit(foot, behind)
        half = math.acos(face[0] * back[0] + face[1] * back[1]) / 2
        along = nose / math.tan(half)  # from the corner to where the nose touches either side
        if along > min(math.dist(foot, top), math.dist(foot, behind)):
            raise ValueError("The nose is too large to lie in a tooth's corner")
        middle = _unit((0.0, 0.0), (face[0] + back[0], face[1] + back[1]))
        reach = nose / math.sin(half)
        return foot[0] + reach * middle[0], foot[1] + reach * middle[1]

    def seated(self, pawl: Pawl, pivot: Point) -> tuple[float, float]:
        """(turn of the wheel, direction of the pawl) with the pawl's nose in a tooth's corner.

        The turn is the one within a pitch, 0 <= turn < pitch; a whole pitch more seats the
        pawl in the next tooth. Raises if a pawl of this length does not reach the teeth.
        """
        seat = self.seat(pawl.nose)
        radius, far = math.hypot(*seat), math.hypot(*pivot)
        if not abs(radius - pawl.length) < far < radius + pawl.length:
            raise ValueError("The pawl does not reach the wheel's teeth from its pivot")
        along = (radius**2 - pawl.length**2 + far**2) / (2 * far)
        # of the two places where the nose can lie, the one counter-clockwise of the pivot
        place = math.degrees(math.atan2(pivot[1], pivot[0]) + math.acos(along / radius))
        nose = _polar(radius, place)
        direction = math.degrees(math.atan2(nose[1] - pivot[1], nose[0] - pivot[0]))
        turn = (place - math.degrees(math.atan2(seat[1], seat[0]))) % self.pitch
        return turn, direction

    def locks(self, pawl: Pawl, pivot: Point) -> float:
        """How surely a tooth's push holds a seated pawl in its corner, in degrees.

        The angle between the face's push on the nose and the line from the nose to the pivot,
        positive when the push turns the pawl towards the root. A pawl stays seated while this
        is larger than minus the angle of friction; with a positive value it needs no friction.
        """
        turn, direction = self.seated(pawl, pivot)
        foot, top, _ = self._tooth
        seat = self.seat(pawl.nose)
        here = math.degrees(math.atan2(seat[1], seat[0])) + turn
        place = math.degrees(math.atan2(*pawl.tip(pivot, direction)[::-1]))
        spin = here + self.pitch * round((place - here) / self.pitch)  # the tooth that is met
        out = _turn(_unit(foot, top), spin - math.degrees(math.atan2(seat[1], seat[0])))
        push = (out[1], -out[0])  # from the face into the gap: clockwise of the face
        arm = _polar(1.0, direction)
        swing = (-arm[1], arm[0])  # the nose's way when the pawl turns counter-clockwise
        inwards = -1.0 if swing[0] * out[0] + swing[1] * out[1] > 0 else 1.0
        across = inwards * (push[0] * swing[0] + push[1] * swing[1])
        return math.degrees(math.atan2(across, -(push[0] * arm[0] + push[1] * arm[1])))

    def falls(
        self,
        pawl: Pawl,
        pivot: Point,
        turn: float,
        start: float,
        stop: float,
        step: float = 0.2,
    ) -> float:
        """Direction in which a pawl comes to rest on the wheel turned by `turn`.

        The pawl is let go pointing in direction `start` and swings towards `stop`, where a
        stop holds it if it meets no tooth on the way. If it starts inside a tooth, it is first
        lifted out against its swing, as a tooth's back does when the wheel turns on. The
        result is within 1e-4 degrees of touching, on the free side.

        This follows a wheel that stands or turns forward. A wheel that turns back brings a
        face against the nose and ends where `seated` has it; because the face is undercut,
        the nose cannot swing straight out of that corner, nor into it: after a whole tooth
        the wheel has to turn a little further before the pawl falls behind the tooth.
        """
        way = 1.0 if stop >= start else -1.0

        def gaps(angles):
            tips = np.array([pawl.tip(pivot, a) for a in angles])
            return self.clearance(tips, pawl.nose, turn)

        def between(free: float, caught: float) -> float:
            while abs(caught - free) > 1e-4:
                middle = (free + caught) / 2
                if gaps([middle])[0] >= 0:
                    free = middle
                else:
                    caught = middle
            return free

        if gaps([start])[0] < 0:
            # finely at first: beside an undercut face the way out can be a narrow one
            fine = step / 50 * np.arange(1, 100)
            lifted = start - way * np.append(fine, step * np.arange(2, int(90 / step)))
            clear = np.flatnonzero(gaps(lifted) >= 0)
            if not clear.size:
                raise ValueError("The pawl cannot be lifted clear of the wheel")
            first = clear[0]
            return between(float(lifted[first]), float(lifted[first - 1]) if first else start)
        count = int(abs(stop - start) / step)
        swept = np.append(start + way * step * np.arange(1, count + 1), stop)
        caught = np.flatnonzero(gaps(swept) < 0)
        if not caught.size:
            return stop
        first = caught[0]
        return between(float(swept[first - 1]) if first else start, float(swept[first]))
