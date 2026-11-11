# Verification record — Carnall 0.1.0 / full

11 November 2026. Parametric build123d geometry; no AI mesh or image generation.

| Check | Result |
|---|---|
| Declared SKU | `carnall / full` |
| Overall assembly | 180 × 90 × 120 mm |
| BRep gate | 49 valid, positive, single-solid components |
| Mesh gate | 49 closed, oriented volumes after removing only zero-area pole triangles |
| Individual build envelope | All components fit the 220 × 220 × 250 mm prototype profile |
| Snapshots | Per-part volume, area, bounds, face and solid counts match the initial baseline |
| Physical moving-part intersections | Zero at 72 poses, 5° apart, through a complete turn |
| Cord versus architecture | Included in the same intersection sweep |
| Rope witness | Excluded from physical intersections; visual marker only |
| Kinematics | Exact rod closure, 16 mm stroke, external tangents and loop length checked |
| Animation | Rigid transforms agree with rebuilt CAD poses; forward/reverse endpoints agree |
| Export readers | STEP, STL, GLB and 3MF re-import checks |
| Reproducibility | CAD artifacts compared across independent processes |
| Traceability | Fixed STEP timestamp, canonical occurrence IDs and 3MF UUIDs/ZIP metadata |
| Palette | Preserved in GLB, 3MF and rendered presentation; STEP carries named geometry |

Run from the repository root:

```sh
uv run pytest -q
uv run ruff check packages projects/carnall examples/check_carnall.py
uv run ruff format --check packages projects/carnall examples/check_carnall.py
uv run cadkit build carnall --all --render --animate
```

Workspace-wide `ruff check .` also reports four unrelated existing findings in
`projects/serce/concept/`: import order, a successive-pair loop and two unused `noqa`
directives. Those source files were left untouched.

The CAD collision tolerance is 0.00001 mm³ positive intersection volume. Boundary contact is
allowed. The sweep samples angles, so it does not certify the full continuous swept volume
between them. Manufacturing clearance, load, fatigue, friction, thermal effects and customer
handling are not simulated. The rendered motion is a kinematic demonstration, not a dynamic
simulation or a substitute for the physical acceptance work in [engineering.md](engineering.md).
