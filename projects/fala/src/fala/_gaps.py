"""What shows between two houses while the wave passes.

The brief allows neighbours to shift against each other, but no distracting gaps and no light
leaks. Measures for the joint on the right of house `index`:

- the pavement joint: its width at pavement level and the step in height across it;
- the lap of the upright edges that a viewer straight in front sees at the joint. The tall
  bay's wing stands in front; behind it are the low bay's facade plate (the walls) and,
  above the low eaves, the verge of the low roof (the roofline). A lap is how far the wing
  covers the edge behind it; below zero it is an open slit of that width;
- daylight: sight lines of a viewer in front that pass between two houses and out at the
  back, below the low eaves. Sky over a roof is not a gap.

The first two are exact, from the poses. Daylight is ray casting on the built model
(`cadkit.visibility`), with the viewer far away.
"""

import numpy as np
from cadkit.visibility import through, triangles_of, view_vector

from fala import _massing as massing
from fala import _wave as wave
from fala._layout import LEAN_DIP, layout

AZIMUTHS = (-60, -45, -30, -20, -10, -5, -2, 0, 2, 5, 10, 20, 30, 45, 60)
ELEVATIONS = (0, 2, 5, 10, 20, 30, 40)


def _at(p, index: int, turn: float | None, x: float, z: float) -> tuple[float, float]:
    """World (x, z) of a point given in the frame of house `index`, z above its pavement."""
    moved = wave.unit_matrix(p, index, turn) @ np.array([x, 0.0, z, 1.0])
    return float(moved[0]), float(moved[2])


def joint(p, index: int, turn: float | None = None) -> tuple[float, float]:
    """Width of the pavement joint on the right of house `index`, and the step up across it."""
    left, right = massing.pavement_edges(p)
    ax, az = _at(p, index, turn, right, 0.0)
    bx, bz = _at(p, index + 1, turn, left, 0.0)
    return bx - ax, bz - az


def laps(p, index: int, turn: float | None = None) -> dict:
    """Laps seen straight on at the joint on the right of house `index`: {"walls": (foot, top),
    "roofline": (foot, top)}, each at the two ends of the height that the wing shares with
    the edge behind it. Negative is an open slit of that width."""
    kinds = massing.kind(p, index), massing.kind(p, index + 1)
    if kinds[0][0] == kinds[1][0]:
        raise ValueError("two bays of the same kind side by side have no wing between them")
    tall = 0 if kinds[0][0] == "A" else 1  # which of the two is the tall bay
    side = 1 if tall == 0 else -1  # the wing's edge faces this way

    def edge(house, hw, foot, top, facing):
        return [_at(p, index + house, turn, facing * hw, z) for z in (foot, top)]

    def x_at(line, z):  # an edge is a straight line: where it crosses height z
        (x0, z0), (x1, z1) = line
        return x0 + (x1 - x0) * (z - z0) / (z1 - z0)

    wing = edge(tall, *massing.front_edges(kinds[tall])["wing"], side)
    result = {}
    names = {"facade": "walls", "verge": "roofline"}
    for name, (hw, foot, top) in massing.front_edges(kinds[1 - tall]).items():
        behind = edge(1 - tall, hw, foot, top, -side)
        low, high = max(wing[0][1], behind[0][1]), min(wing[1][1], behind[1][1])
        result[names[name]] = tuple(side * (x_at(wing, z) - x_at(behind, z)) for z in (low, high))
    return result


def survey(p, step: float = 5.0) -> dict:
    """Extremes through one pass of the wave: the pavement joint's width and step, and the
    smallest and largest lap of the walls and of the roofline."""
    widths, steps = [], []
    found = {"walls": [], "roofline": []}
    turn = 0.0
    while turn < 360.0 * p.ratio:
        for i in range(p.houses - 1):
            width, rise = joint(p, i, turn)
            widths.append(width)
            steps.append(abs(rise))
            for name, ends in laps(p, i, turn).items():
                found[name] += ends
        turn += step
    result = {"joint_min": min(widths), "joint_max": max(widths), "step_max": max(steps)}
    for name, values in found.items():
        result[f"{name}_min"], result[f"{name}_max"] = min(values), max(values)
    return result


def daylight(built: dict, p, spacing: float = 0.1, azimuths=AZIMUTHS, elevations=ELEVATIONS):
    """Sight lines from the front that pass between two houses: {(azimuth, elevation):
    (walls, street)}, the number of clear lines in each band. Empty if there are none.

    The lines are taken on a grid in the facade plane (Y = 0), `spacing` apart along the
    street from the first house's centre to the last. Two bands of height: `street`, from
    below the pavement to just above its highest point, where the facade plates stand a
    little clear of the neighbour's pavement (rows 0.25 apart); and `walls`, from there to
    the lowest position of the low eaves (rows 1 apart). Above that the houses differ in
    height and a clear line is sky over a roof.
    """
    L = layout(p)
    xs = np.arange(L.centres[0], L.centres[-1] + spacing / 2, spacing)
    split = p.amplitude + 1.0
    eaves = massing.B_EAVES - p.amplitude - LEAN_DIP - 0.5
    zs = np.concatenate([np.arange(-split, split, 0.25), np.arange(split, eaves, 1.0)])
    grid = np.array([[x, 0.0, z] for x in xs for z in zs])
    street = np.tile(zs < split, len(xs))
    blockers = triangles_of(built.values(), 0.05)
    found = {}
    for azimuth in azimuths:
        for elevation in elevations:
            clear = through(grid, view_vector(azimuth, elevation), blockers)
            if clear.any():
                found[(azimuth, elevation)] = (
                    int((clear & ~street).sum()),
                    int((clear & street).sum()),
                )
    return found
