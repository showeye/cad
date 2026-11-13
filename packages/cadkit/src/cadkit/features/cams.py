"""Corkscrew cam: a round bar whose centre winds around its shaft, and what rides on it.

The cam is defined by circular sections in planes normal to X. Their centres lie at
(e cos(kx - phase), e sin(kx - phase)) from the shaft axis, so the bar's upper edge, seen from
the side, is the travelling sine `crest`. A follower pad whose nose is a cylinder with its axis
along Y (a crowned pad) touches that edge at one point; because the pad is straight along Y,
the sideways swing of the bar slides under it without lifting it. The contact is therefore a
plane problem in X and Z and is solved exactly here: no sampling, no fixed contact station.

Lengths in mm, public angles in degrees. Rigid geometry only: no friction or compliance.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass

from build123d import Plane, Solid, Wire


@dataclass(frozen=True)
class Seat:
    """A rigid follower resting on the cam with two crowned pads.

    `height` is the follower origin above the shaft axis, `lean` its tilt about Y (positive
    lifts the +X end), `contacts` the two touching points as (x, y, z) from the shaft axis.
    """

    height: float
    lean: float
    contacts: tuple[tuple[float, float, float], tuple[float, float, float]]


@dataclass(frozen=True)
class CorkscrewCam:
    """Section radius, eccentricity of the section centres and wavelength along the shaft."""

    radius: float
    eccentricity: float
    wavelength: float

    def __post_init__(self):
        if not all(math.isfinite(v) for v in (self.radius, self.eccentricity, self.wavelength)):
            raise ValueError("Cam dimensions must be finite")
        if not 0 <= self.eccentricity < self.radius or self.wavelength <= 0:
            raise ValueError("Require 0 <= eccentricity < radius and a positive wavelength")
        if self.eccentricity * self.k >= 0.5:
            raise ValueError("Cam slope must stay below 0.5 for the crowned-pad solution")

    @property
    def k(self) -> float:
        """Angular spatial frequency, radians per mm."""
        return math.tau / self.wavelength

    def centre(self, x: float, phase: float) -> tuple[float, float]:
        """Y and Z of the section centre at X, from the shaft axis."""
        a = self.k * x - math.radians(phase)
        return self.eccentricity * math.cos(a), self.eccentricity * math.sin(a)

    def crest(self, x: float, phase: float, upper: bool = True) -> float:
        """Height of the bar's upper (or lower) edge above the shaft axis at X."""
        return self.centre(x, phase)[1] + (self.radius if upper else -self.radius)

    def slope(self, x: float, phase: float) -> float:
        """Rise of the edge per mm along the shaft at X."""
        return self.eccentricity * self.k * math.cos(self.k * x - math.radians(phase))

    def rider(
        self, x: float, phase: float, crown: float = 0.0, upper: bool = True
    ) -> tuple[float, float]:
        """Where the centre of a pad nose of radius `crown` sits when the nose is at X.

        Returns (height of the nose centre above the shaft axis, X of the touching point).
        An upper pad rests on the bar, a lower pad hangs below it. The centre travels on the
        curve parallel to the edge at the crown radius; the touching point is found by a
        contraction that converges because crown * curvature is far below one.
        """
        if crown < 0 or not math.isfinite(crown):
            raise ValueError("Crown radius must be finite and not negative")
        side = 1.0 if upper else -1.0
        touch = x
        for _ in range(60):
            angle = math.atan(self.slope(touch, phase))
            new = x + side * crown * math.sin(angle)
            if abs(new - touch) < 1e-13:
                touch = new
                break
            touch = new
        angle = math.atan(self.slope(touch, phase))
        return self.crest(touch, phase, upper) + side * crown * math.cos(angle), touch

    def seat(
        self,
        x: float,
        phase: float,
        pads: Sequence[tuple[float, float]],
        crown: float,
    ) -> Seat:
        """Rest a follower on the bar: its origin stays at X, it rises and leans about Y.

        `pads` are the two nose centres (u along the follower, w up) in the follower's own
        frame. The lean at which both noses touch is unique; it is bracketed and bisected.
        """
        if len(pads) != 2 or pads[0][0] >= pads[1][0]:
            raise ValueError("Give two pads, ordered along the follower")

        def lift(theta, pad):
            u, w = pad
            c, s = math.cos(theta), math.sin(theta)
            height, touch = self.rider(x + u * c - w * s, phase, crown)
            return height - u * s - w * c, touch

        low, high = -math.atan(0.6), math.atan(0.6)
        for _ in range(80):
            theta = (low + high) / 2
            if lift(theta, pads[1])[0] > lift(theta, pads[0])[0]:
                low = theta
            else:
                high = theta
        theta = (low + high) / 2
        (height, first), (_, second) = lift(theta, pads[0]), lift(theta, pads[1])
        contacts = tuple(
            (t, self.centre(t, phase)[0], self.crest(t, phase)) for t in (first, second)
        )
        return Seat(height, math.degrees(theta), contacts)

    def gap_below(
        self,
        x: float,
        phase: float,
        height: float,
        lean: float,
        pad: tuple[float, float],
        crown: float,
    ) -> float:
        """Clearance between the bar and a lower pad of a follower in the given pose.

        `pad` is the nose centre of the lower pad in the follower frame. Negative means the
        follower is squeezed between its upper and lower pads.
        """
        theta = math.radians(lean)
        c, s = math.cos(theta), math.sin(theta)
        u, w = pad
        centre_x, centre_z = x + u * c - w * s, height + u * s + w * c
        # nearest point of the lower edge to the nose centre: a short Newton search
        touch = centre_x
        for _ in range(40):
            dz = self.crest(touch, phase, upper=False) - centre_z
            slope = self.slope(touch, phase)
            bend = -self.eccentricity * self.k**2 * math.sin(self.k * touch - math.radians(phase))
            step = ((touch - centre_x) + dz * slope) / (1 + slope * slope + dz * bend)
            touch -= step
            if abs(step) < 1e-13:
                break
        edge = self.crest(touch, phase, upper=False)
        return math.hypot(touch - centre_x, edge - centre_z) - crown

    def solid(self, start: float, end: float, spacing: float = 2.0) -> Solid:
        """The bar from X = start to end at phase 0, about the X axis: a loft through sections."""
        if end <= start or spacing <= 0:
            raise ValueError("Require end > start and a positive section spacing")
        count = max(3, math.ceil((end - start) / spacing) + 1)
        wires = []
        for i in range(count):
            x = start + (end - start) * i / (count - 1)
            y, z = self.centre(x, 0.0)
            wires.append(Wire.make_circle(self.radius, Plane(origin=(x, y, z), z_dir=(1, 0, 0))))
        return Solid.make_loft(wires)
