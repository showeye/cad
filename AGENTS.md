# AGENTS.md

Single source of agent instructions for every harness (Codex, Cursor and others read this file directly; `CLAUDE.md` imports it). Edit only this file.

Commercial CAD monorepo: parametric models built with **build123d**, managed with **uv**. The models are sold, so quality, traceability and reproducibility come first. Every project builds on one shared package (`cadkit`) so new products are fast and cheap to write.

## Structure (target)

```
cad/
├── pyproject.toml            # uv workspace root (virtual), dev tools, ruff/pytest config
├── AGENTS.md
├── packages/
│   └── cadkit/               # THE shared library; all reusable code lives here
│       └── src/cadkit/
│           ├── params.py     # Params base (pydantic, frozen, validated; mm / degrees)
│           ├── model.py      # Model base class + entry-point discovery
│           ├── process.py    # FDM / SLA / CNC profiles: tolerances, build volume, mesh quality
│           ├── standards/    # ISO reference data (fasteners, inserts, bearings, …)
│           ├── features/     # reusable geometry: holes, pockets, fillets, joints, text, …
│           ├── validate.py   # quality gate: valid BRep, single solid, watertight, fits build volume
│           ├── export.py     # STEP/STL/3MF/GLB + manifest.json (params, metrics, sha256, git rev)
│           ├── render.py     # offscreen PNG renders for listings; OCP viewer helper
│           ├── testing.py    # standard pytest suite + geometry snapshots
│           └── cli.py        # `cadkit list | build | show | new`
└── projects/
    └── <product>/            # one sellable product = one workspace package
        ├── pyproject.toml    # depends on cadkit; registers entry point "cadkit.models"
        ├── src/<product>/model.py   # Params + variants + build(); geometry only
        └── tests/            # one-line cadkit suite + snapshots/<variant>.json
```

Build outputs go to `dist/<model>/<version>/<variant>/` (gitignored).

## Strategy

1. **Projects hold only product geometry.** Params, validation, export, rendering, tests and CLI come from `cadkit`. If a project needs plumbing, add it to `cadkit`.
2. **Where new code goes:**
   - **Generic → `cadkit` immediately:** standards data, fastener and joint features, process tolerances, and anything else that doesn't depend on this product's design. It needs tests and a docstring.
   - **Product-specific → the project:** shapes and proportions that belong to this product only.
   - **Unsure → the project's `_shared.py`:** move it to `cadkit` once a second project needs it, and generalize it at that point, not before.
   - Never copy code between projects. Copying is the signal to move it into `cadkit`.
3. **Check cadkit first.** Before writing geometry, read the `cadkit` module index (above) and the module docstrings. Read whole files only when needed, to keep token usage low.
4. **The model contract:** a `Params` subclass, a `variants` dict (sellable SKUs), a `process`, a `version`, and `build(params) -> Shape | dict[part, Shape]`. Everything else stays private.
5. **Units:** mm and degrees everywhere. Bounds are enforced through pydantic `Field` constraints and validators, so bad inputs fail before the CAD kernel runs.
6. **Feature-tool convention:** cutting tools sit at z=0 and point -Z, with a small overshoot. Position them with `Pos`/`Plane` and subtract them.
7. **Standards data:** cite the source (ISO number) in the module. Vendor data (e.g. heat-set inserts) must be marked "verify against datasheet".

## Quality gates (non-negotiable)

- Every variant must build, pass `validate` with zero errors, and match its geometry snapshot (volume, area, bbox, solid/face count).
- Intended geometry change: bump the model `version`, then regenerate snapshots (`CADKIT_UPDATE_SNAPSHOTS=1`). Never change a released `name` or variant key, because they form the SKU.
- Exports are deterministic (fixed STEP timestamp). `manifest.json` records params, metrics, file hashes, library versions and the git commit.
- `cadkit` changes must not alter existing snapshots unless that is intended. Run the full workspace test suite.

## Workflow

```
uv sync --all-packages          # after adding a project
uv run cadkit new <product>     # scaffold from template
uv run cadkit show <product> -v <variant>
uv run pytest                   # all packages + projects
uv run ruff check . && uv run ruff format .
uv run cadkit build <product> --all --render
```

Python 3.12, ruff (line length 100). Commit only when asked.
