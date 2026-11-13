"""Fala, motion proof: the long checks and the pictures that docs/motion-proof.md quotes.

Run from the repository root:

    uv run cadkit build fala -v nikisz --animate               # exports, stills, the two films
    uv run python projects/fala/tools/motion_proof.py checks   # about 8 minutes on 6 cores
    uv run python projects/fala/tools/motion_proof.py assets   # pictures into docs/img/motion

`checks` goes through one pass of the wave and writes docs/motion-proof-checks.json:

- collisions between all parts at the 72 poses of the film;
- what a viewer in front sees of the mechanism (`fala._hidden`): 12 poses, 152 directions;
- daylight between the houses (`fala._gaps`): 12 poses, 105 directions;
- whether each house goes in from above, with the handwheel on the crest and off it;
- the exact measures: the wave, the pavement joint, the laps, and the force model's table.

`assets` copies the renders from dist/ into docs/img/motion, scaled for the document.
"""

import json
import math
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from build123d import Pos
from cadkit.validate import overlaps
from fala import _gaps as gaps
from fala import _hidden as hidden
from fala import _massing as massing
from fala import _statics as statics
from fala import _wave as wave
from fala.model import FRAMES, Params, build, model
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DIST = ROOT.parents[1] / "dist" / model.name / model.version / "nikisz"
P = Params()
PASS = 360.0 * P.ratio
FRICTIONS = (0.1, 0.2, 0.25, 0.3, 0.35, 0.45, 0.55, 0.6)
OFF_CREST = (-40.0, 0.0, 60.0, 140.0)  # handwheel angles from the crest at which a house goes in
DROP = (60.0, 45.0, 35.0, 25.0, 20.0, 15.0, 12.0, 10.0, 8.0, 6.0, 4.0, 3.0, 2.0, 1.0, 0.5)


def _collide(turn):
    return turn, overlaps(build(Params(turn=turn)))


def _mechanism(turn):
    p = Params(turn=turn)
    found = hidden.exposed(build(p), p)
    return turn, {name: [seen, of, views] for name, (seen, of, views) in found.items()}


def _daylight(turn):
    p = Params(turn=turn)
    return turn, [[*view, *counts] for view, counts in gaps.daylight(build(p), p).items()]


def _goes_in(job):
    """Lower house `index` straight down with the handwheel `off` degrees from its crest."""
    index, off = job
    built = build(Params(turn=wave.crest(P, index) + off))
    name = f"house_{index + 1}"
    placed = {
        k: v
        for k, v in built.items()
        if not k.startswith("house_") or int(k.split("_")[1]) <= index
    }
    hits = [
        (lift, found)
        for lift in DROP
        if (found := overlaps({**placed, name: Pos(0, 0, lift) * built[name]}, moving={name}))
    ]
    return (index + 1, off), hits


def _friction(mu):
    # a pose with no balance has no finite torque: store it as null
    return mu, {k: v if math.isfinite(v) else None for k, v in statics.survey(P, mu).items()}


def _wave():
    poses = [wave.pose(P, i, t) for i in range(P.houses) for t in range(0, int(PASS), 5)]
    lean = max(abs(at.lean) for at in poses)
    sway = lambda top: 2 * (top + P.pivot_drop) * math.sin(math.radians(lean))  # side to side
    return {
        "rise": max(at.rise for at in poses) - min(at.rise for at in poses),
        "lean": lean,
        "capture_min": min(at.gap for at in poses),
        "capture_max": max(max(at.gaps) for at in poses),
        "sway_tall_chimney": sway(massing.A_CHIMNEY[4]),
        "sway_low_chimney": sway(massing.B_CHIMNEY[4]),
        "crests": [wave.crest(P, i) for i in range(P.houses)],
        "masses": {k: statics.unit_mass(P, k)[0] for k in ("A", "B", "AL", "BR")},
    }


def checks(workers: int = 6):
    film = [PASS * k / FRAMES for k in range(FRAMES)]
    twelve = [PASS * k / 12 for k in range(12)]
    result = {"version": model.version, "wave": _wave(), "gaps": gaps.survey(P)}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        jobs = {
            "collisions": pool.map(_collide, film),
            "mechanism_seen": pool.map(_mechanism, twelve),
            "daylight": pool.map(_daylight, twelve),
            "goes_in": pool.map(_goes_in, [(i, off) for off in OFF_CREST for i in range(P.houses)]),
            "friction": pool.map(_friction, FRICTIONS),
        }
        for name, found in jobs.items():
            result[name] = {str(key): value for key, value in found}
            bad = {k: v for k, v in result[name].items() if v} if name != "friction" else {}
            print(f"{name}: {len(result[name])} runs, {'clear' if not bad else bad}", flush=True)
    path = DOCS / "motion-proof-checks.json"
    path.write_text(json.dumps(result, indent=1) + "\n")
    print(path)


def assets():
    out = DOCS / "img" / "motion"
    out.mkdir(parents=True, exist_ok=True)
    for name in ("hero", "front", "top", "back", "mechanism", "mechanism_front"):
        with Image.open(DIST / f"{name}.png") as image:
            image = image.convert("RGB")
            image.thumbnail((1200, 800), Image.Resampling.LANCZOS)
            image.save(out / f"{name}.jpg", quality=88)
    # the wave at four phases of one pass, one under the other
    phases = [Image.open(DIST / f"phase_{i}.png").convert("RGB") for i in range(4)]
    width = 1000
    rows = [
        im.resize((width, im.height * width // im.width), Image.Resampling.LANCZOS) for im in phases
    ]
    strip = Image.new("RGB", (width, sum(r.height for r in rows)), "white")
    y = 0
    for row in rows:
        strip.paste(row, (0, y))
        y += row.height
    strip.save(out / "phases.jpg", quality=88)
    # the two films, half size and every second pose: light enough for the repository
    for film, folder in (("motion", "frames"), ("mechanism", "frames_mechanism")):
        frames = sorted((DIST / folder).glob("*.png"))[:-1][::2]
        images = [
            Image.open(f).convert("RGB").resize((560, 350), Image.Resampling.LANCZOS)
            for f in frames
        ]
        images = [im.quantize(colors=96, method=Image.Quantize.MEDIANCUT) for im in images]
        images[0].save(
            out / f"{film}.gif",
            save_all=True,
            append_images=images[1:],
            duration=160,
            loop=0,
            optimize=True,
        )
    for path in sorted(out.iterdir()):
        print(f"{path.stat().st_size / 1e6:6.2f} MB  {path.name}")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else ""
    if what not in ("checks", "assets"):
        sys.exit(__doc__)
    checks() if what == "checks" else assets()
