"""Rigid transforms, planar slider-cranks and open belts; mm and degrees throughout."""

import math
from dataclasses import dataclass

import numpy as np


def rigid_transform(axis=(0, 0, 1), origin=(0, 0, 0), angle=0, shift=(0, 0, 0)):
    """Homogeneous right-handed axis rotation followed by translation, in mm/degrees.

    The rotation axis passes through ``origin``. The returned nested lists can be
    serialised as rigid presentation poses without changing the original CAD mesh.
    """
    k, centre, translation = (np.asarray(v, dtype=float) for v in (axis, origin, shift))
    if any(v.shape != (3,) or not np.isfinite(v).all() for v in (k, centre, translation)):
        raise ValueError("Finite three-dimensional vectors required")
    if not math.isfinite(angle) or np.linalg.norm(k) == 0:
        raise ValueError("Finite angle and nonzero rotation axis required")
    k = k / np.linalg.norm(k)
    x, y, z = k
    cross = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
    t = math.radians(angle)
    rotation = np.eye(3) + math.sin(t) * cross + (1 - math.cos(t)) * cross @ cross
    result = np.eye(4)
    result[:3, :3] = rotation
    result[:3, 3] = centre - rotation @ centre + translation
    return result.tolist()


def slider_crank(radius: float, rod: float, angle: float) -> tuple[float, float, float]:
    """Return crank x/z and left-hand slider x relative to shaft; no offset."""
    if not 0 < radius < rod:
        raise ValueError("Require 0 < crank radius < connecting-rod length")
    t = math.radians(angle)
    x, z = radius * math.cos(t), radius * math.sin(t)
    return x, z, x - math.sqrt(rod * rod - z * z)


@dataclass(frozen=True)
class Belt:
    """Two externally tangent pulley circles in a common XY plane."""

    c1: tuple[float, float]
    r1: float
    c2: tuple[float, float]
    r2: float

    def __post_init__(self):
        if min(self.r1, self.r2) <= 0 or self.distance <= self.r1 + self.r2:
            raise ValueError("Require positive radii and separate pulleys")

    @property
    def distance(self) -> float:
        return math.dist(self.c1, self.c2)

    @property
    def normal_angles(self) -> tuple[float, float]:
        """External tangent normals in radians, lower then upper."""
        phi = math.atan2(self.c2[1] - self.c1[1], self.c2[0] - self.c1[0])
        alpha = math.acos((self.r1 - self.r2) / self.distance)
        return phi - alpha, phi + alpha

    def points(self, arc_steps: int = 80) -> list[tuple[float, float]]:
        """Ordered closed loop with straight tangents and sampled contact arcs."""
        low, high = self.normal_angles
        pts = []
        for centre, radius, start, stop in (
            (self.c1, self.r1, high, low + 2 * math.pi),
            (self.c2, self.r2, low, high),
        ):
            for i in range(arc_steps + 1):
                a = start + (stop - start) * i / arc_steps
                pts.append((centre[0] + radius * math.cos(a), centre[1] + radius * math.sin(a)))
        return pts + [pts[0]]

    @property
    def length(self) -> float:
        """Exact neutral-line length, excluding any cord stretch."""
        low, high = self.normal_angles
        straight = math.sqrt(self.distance**2 - (self.r1 - self.r2) ** 2)
        return 2 * straight + self.r1 * (2 * math.pi - high + low) + self.r2 * (high - low)

    def point_at(self, travel: float) -> tuple[float, float]:
        """Exact distance parameter along the contact arcs and straight tangents."""
        low, high = self.normal_angles
        straight = math.sqrt(self.distance**2 - (self.r1 - self.r2) ** 2)
        arc1 = self.r1 * (2 * math.pi - high + low)
        arc2 = self.r2 * (high - low)
        remaining = travel % self.length
        for centre, radius, start, length, next_centre, next_radius in (
            (self.c1, self.r1, high, arc1, self.c2, self.r2),
            (self.c2, self.r2, low, arc2, self.c1, self.r1),
        ):
            if remaining <= length:
                angle = start + remaining / radius
                return centre[0] + radius * math.cos(angle), centre[1] + radius * math.sin(angle)
            remaining -= length
            angle = low if centre == self.c1 else high
            a = tuple(c + radius * v for c, v in zip(centre, (math.cos(angle), math.sin(angle))))
            b = tuple(
                c + next_radius * v for c, v in zip(next_centre, (math.cos(angle), math.sin(angle)))
            )
            if remaining <= straight:
                t = remaining / straight
                return a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])
            remaining -= straight
        return self.point_at(0)
