"""Finite flat-pad contact on a circular-section eccentric helical cam.

The cam is a loft of circles in planes normal to X, not a circular tube swept
normal to a helix. Lengths are mm; public angles are degrees. These equations
describe rigid, frictionless geometry, not compliance or a friction prediction.
"""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class PadPose:
    """A rigid carriage, its two upper contacts and lower-jaw clearances."""

    height: float
    lean: float
    contacts: tuple[tuple[float, float, float], ...]
    return_gaps: tuple[float, float]


@dataclass(frozen=True)
class HelicalCam:
    """Circle centres (e cos(kx-phase), e sin(kx-phase)) about the X axis."""

    radius: float
    eccentricity: float
    wavelength: float

    def __post_init__(self):
        if not all(math.isfinite(v) for v in (self.radius, self.eccentricity, self.wavelength)):
            raise ValueError("Cam dimensions must be finite")
        if not 0 <= self.eccentricity < self.radius or self.wavelength <= 0:
            raise ValueError("Require 0 <= eccentricity < radius and positive wavelength")

    @property
    def k(self):
        """Angular spatial frequency, radians/mm."""
        return math.tau / self.wavelength

    def centre(self, x: float, phase: float) -> tuple[float, float]:
        """Y/Z centre of the section at X and shaft phase in degrees."""
        a = self.k * x - math.radians(phase)
        return self.eccentricity * math.cos(a), self.eccentricity * math.sin(a)

    def _extreme(self, x, phase, theta, offset, interval, upper):
        """Extremum of required deck height over a finite pad in local X.

        A contact on local z=-offset has global x=x0+u cos(theta)+offset
        sin(theta). Enumerate both edges and every stationary point, including
        multiple wavelengths; no sampling or fixed contact station is used.
        """
        c, s = math.cos(theta), math.sin(theta)
        a = self.k * (x + offset * s) - math.radians(phase)
        b = self.k * c
        candidates = list(interval)
        if self.eccentricity:
            target = s / (self.eccentricity * b)
            if abs(target) <= 1:
                alpha = math.acos(target)
                for root in (alpha, -alpha):
                    first = math.ceil((a + b * interval[0] - root) / math.tau)
                    last = math.floor((a + b * interval[1] - root) / math.tau)
                    candidates.extend((root + n * math.tau - a) / b for n in range(first, last + 1))
        values = [
            (
                self.eccentricity * math.sin(a + b * u)
                + (self.radius if upper else -self.radius)
                - u * s
                + offset * c,
                u,
            )
            for u in candidates
        ]
        return (max if upper else min)(values)

    def _return_gap(self, x, phase, theta, height, offset, interval):
        """Minimum normal gap with the cam projected inside the finite lower face.

        The surface projection, rather than the face's world-X footprint, is
        bounded here: a nonzero return gap shifts the projection along local X.
        """
        c, s = math.cos(theta), math.sin(theta)

        def local_u(xx):
            z = self.centre(xx, phase)[1] - self.radius
            return c * (xx - x) + s * (z - height)

        endpoints = []
        margin = abs(s) * (self.eccentricity + self.radius + abs(height)) / c + 1
        for u in interval:
            low, high = x + u / c - margin, x + u / c + margin
            for _ in range(50):
                mid = (low + high) / 2
                if local_u(mid) > u:
                    high = mid
                else:
                    low = mid
            endpoints.append((low + high) / 2)
        candidates = list(endpoints)
        if self.eccentricity:
            target = s / (self.eccentricity * self.k * c)
            if abs(target) <= 1:
                alpha = math.acos(target)
                phi = math.radians(phase)
                for root in (alpha, -alpha):
                    first = math.ceil((self.k * endpoints[0] - phi - root) / math.tau)
                    last = math.floor((self.k * endpoints[1] - phi - root) / math.tau)
                    candidates.extend(
                        (root + phi + n * math.tau) / self.k for n in range(first, last + 1)
                    )
        return min(
            -s * (xx - x) + c * (self.centre(xx, phase)[1] - self.radius - height) + offset
            for xx in candidates
        )

    def flat_pads(self, x, phase, span, width, depth, opening, pad_depth) -> PadPose:
        """Seat two coplanar upper pads under gravity and check captured lower faces.

        The carriage origin stays at fixed X and translates in Z. It can rock
        about Y. Pads centred at local X=+/-span/2 are width wide along X and
        pad_depth wide along Y, with their underside at local Z=-depth. The
        lower faces are opening below these. Contacts slide in X and Y;
        fixing their world X coordinates would overconstrain a rigid carriage.

        Full-width contact requires pad_depth/2 >= eccentricity. Return gaps
        are measured normal to the pads in the gravity-seated pose. A negative
        value means interference. They are not total free-rocking backlash.
        """
        values = (x, phase, span, width, depth, opening, pad_depth)
        if not all(math.isfinite(v) for v in values):
            raise ValueError("Pad dimensions and pose must be finite")
        if not 0 < width < span or min(depth, opening, pad_depth) <= 0:
            raise ValueError("Require 0 < pad width < span and positive depth/opening")
        if pad_depth < 2 * self.eccentricity:
            raise ValueError("Pad is too narrow for full-width contact")
        if self.eccentricity * self.k >= 0.5:
            raise ValueError("Flat-pad solver is limited to cam slopes below 0.5")
        intervals = tuple((u - width / 2, u + width / 2) for u in (-span / 2, span / 2))

        def upper(theta):
            return tuple(self._extreme(x, phase, theta, depth, r, True) for r in intervals)

        low, high = -math.atan(0.5), math.atan(0.5)
        for _ in range(60):
            theta = (low + high) / 2
            left, right = upper(theta)
            if left[0] > right[0]:
                high = theta
            else:
                low = theta
        theta = (low + high) / 2
        points = upper(theta)
        height = sum(p[0] for p in points) / 2
        c, s = math.cos(theta), math.sin(theta)
        contacts = []
        for _, u in points:
            xx = x + u * c + depth * s
            yy, zz = self.centre(xx, phase)
            contacts.append((xx, yy, zz + self.radius))
        gaps = tuple(
            self._return_gap(x, phase, theta, height, depth + opening, r) for r in intervals
        )
        return PadPose(height, math.degrees(theta), tuple(contacts), gaps)
