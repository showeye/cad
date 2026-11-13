# Fala (The Wave)

A hand-cranked collector piece: a Nikisz-style terrace of Silesian familoks on
ground that rolls like a wave.

## Current stage — 2026-11-13

**Nikisz and drive A (corkscrew) are approved for development.** Stage 3B adds
serviceable axle/guide retention, labelled 0.30/0.40/0.50 mm U1 fit coupons,
explicit print orientations and removable ballast masts to the two-carriage rig.
The current model is **0.2.0**; variant `contact_rig` keeps its existing key.

- [U1 test package: orientation, BOM, assembly and measurements](docs/u1-test-guide.md)
- [Fit-coupon CAD preview, shown in bed orientation](docs/img/u1_fit_040.png)
- [Rig, animation, contact solution and next gates](docs/contact-rig.md)
- [Contact evidence](docs/contact-proof.json) and [load-fixture clearance evidence](docs/loaded-proof.json)
- [Verification record and known limits](docs/verification.md)
- [Earlier drive comparison](docs/drive-comparison.md)

The rig develops the mechanism before the decorated terrace. Retention is now
modelled; physical fit, loaded effort, noise and endurance still need tests.
The oriented 3MFs require support painting and slicer inspection before printing.
No production release or measured print time is claimed.

## Files

| Path | Contents |
|---|---|
| `docs/brief.md` | Client brief, verbatim; source of truth |
| `docs/look-brief.md` | Research, references, palette and original concepts; the client subsequently chose Nikisz |
| `docs/design-notes.md` | Historical engineering starting points |
| `docs/drive-comparison.md` | Approved drive direction and screening limitations |
| `docs/contact-rig.md` | Current contact engineering, evidence and staged acceptance gates |
| `docs/u1-test-guide.md` | Fit ladder, orientation/support rules, retention hardware, assembly and loaded test |
| `docs/u1-fit-results.csv`, `docs/u1-results.csv` | Blank fit and loaded-test records |
| `docs/verification.md` | Completed checks and existing repository lint issues |
| `src/fala/model.py` | Parametric rig geometry, validated dimensions and rigid poses |
| `engineering/prove_contact.py` | Contact/collision evidence; calls shared export/render tools |
| `engineering/prepare_u1.py` | Oriented test geometry, manifests and review ZIPs through cadkit |
| `engineering/compare_drives.py` | Earlier prescribed-path screening study |
| `tests/` | Contact, rigid-motion, parameter and shared quality/snapshot checks |
| `concept/` | Historical massing scripts; not product geometry |
| `research/` | Reference photos, contact sheets and source/licence records |
| `dist/` | Reproducible local CAD/Blender outputs (gitignored) |

## Work with the current model

Run from the repository root:

```
uv sync --all-packages
uv run cadkit list
uv run cadkit show fala -v contact_rig
uv run pytest
uv run python projects/fala/engineering/prove_contact.py
uv run python projects/fala/engineering/prove_contact.py --variant loaded_rig
uv run python projects/fala/engineering/prepare_u1.py --render
```

The proof commands check signed full rotations at 1° intervals and regenerate
the evidence. The final command exports all five variants, renders their actual
CAD and saves forward/reverse rig animations. Each export includes `print/`
with oriented 3MF, individual STEP/STL and a linked manifest; each variant also
has a review ZIP. Exports stay under `projects/fala/dist/fala/0.2.0/`.
The VS Code OCP CAD Viewer listens on port 3939.

To regenerate the older concept material:

```
uv run python projects/fala/concept/look_concepts.py --strip
uv run python projects/fala/concept/compose_sheets.py
uv run python projects/fala/concept/mechanism_diagrams.py
```

## Handoff

Read `AGENTS.md`, `docs/brief.md` and `docs/contact-rig.md`. Continue Nikisz and
corkscrew A without repeating drive selection. B remains the fallback if loaded
contact tests fail.

Next, inspect the proposed support placements in Snapmaker Orca, print the U1
fit ladder using the guide, and return actual fit measurements before tuning
the rig. Then weigh/balance the moving assemblies and run the loaded comparison.
The revised flat-print mast has nominal adjustment range for the assumed load;
actual mass/CG and the purchased ballast pack still need checking.
Broad upper contacts seat geometrically; the roughly 0.33–0.50 mm return
clearance is not a measurement of free rocking or
real print fit. The pin and keel are centred in their clearances during the study.

The full terrace still needs concealed joints, roof clearance, transmission and
overload design. Keep the provisional 3:1 ratio explicitly unconfirmed. Lettering,
rear panel, ballast and filament brand remain open and need not block rig work.

All Fala materials stay in this project directory. Reusable mechanics and
plumbing belong in `cadkit`. Third-party research photos must stay out of shipped
or published material; see `research/SOURCES.md`. Commit only when requested.
