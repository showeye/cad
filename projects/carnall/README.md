# Na szychcie od 1915

A hand-cranked Carnall winding engine in a cutaway brick engine house. Full form:
**180 × 90 × 120 mm**, version **0.1.0**, variant **full**. The magnet is outside this edition.

![CAD concept](../../dist/carnall/0.1.0/full/hero.png)

Turn the ochre grip on the front crank pin. The large rope wheel turns, two quartered
connecting rods swing, both piston/crosshead units slide 16 mm, and a continuous cord drives
the upper sheave. Open cylinder sections reveal the piston heads. The headframe remains a
backdrop; there is no cage or character transformation in this edition.

This is a **parametric engineering concept**, not a physically proven product. Geometry,
sampled motion and export quality are checked. Fit, shaft strength, friction, cord grip,
fastener retention, endurance and assembly time still require a printed prototype.

| Review material | Location |
|---|---|
| Downloadable review package | [carnall-0.1.0-full.zip](../../dist/carnall/0.1.0/carnall-0.1.0-full.zip) |
| Research, references, selling hypotheses and copy | [docs/research.md](docs/research.md) |
| Mechanism, assembly and prototype plan | [docs/engineering.md](docs/engineering.md) |
| Verification record | [docs/verification.md](docs/verification.md) |
| Concept sheet | [concept-sheet.jpg](../../dist/carnall/0.1.0/full/concept-sheet.jpg) |
| Forward and reverse motion | [motion.gif](../../dist/carnall/0.1.0/full/motion.gif) |
| CAD assembly | [assembly.step](../../dist/carnall/0.1.0/full/assembly.step) |
| Coloured assembly reference | [assembly.glb](../../dist/carnall/0.1.0/full/assembly.glb) |
| 3MF assembly reference | [assembly.3mf](../../dist/carnall/0.1.0/full/assembly.3mf) |
| Individual component meshes | [parts](../../dist/carnall/0.1.0/full/parts/) |
| Animated Blender presentation | [presentation.blend](../../dist/carnall/0.1.0/full/presentation.blend) |
| Parameters, quality metrics and hashes | [manifest.json](../../dist/carnall/0.1.0/full/manifest.json) |

The 3MF and STLs use assembly coordinates. **They are not support-free production plates.**
The flexible cord and visual witness marker are omitted from printable parts. STEP and GLB
include both as references. All modelling is build123d BRep; the images use the actual CAD mesh.

## Build and inspect

From the repository root:

```sh
uv sync --all-packages
uv run cadkit list
uv run cadkit show carnall -v full
uv run cadkit build carnall --all --render --animate
uv run pytest
uv run ruff check packages projects/carnall examples/check_carnall.py
```

Blender is required for rendering. It runs in a separate background process and saves its
own scene, leaving the live Blender scene alone. The OCP viewer is optional for `show`.
Render output and all exported models are under `dist/`, which is gitignored.

Geometry lives in [src/carnall/model.py](src/carnall/model.py). Shared features, typography,
validation, snapshots, CLI, exports and rendering live in `packages/cadkit`.
The bundled OFL typeface makes the plate independent of system fonts.

The sole SKU is `carnall / full`; the quartering, arched windows and compressed headframe
are deliberate stylisation, not a measured replica. Future museum editions must change
their own dates and facts as well as the replaceable nameplate.
