# Fala (The Wave)

A hand-cranked collector piece: a Nikisz-style terrace of Silesian familoks on
ground that rolls like a wave.

## Current stage — 2026-11-13

**Nikisz and drive A (corkscrew) are approved for development.** Stage 3A now has
a parametric two-carriage contact rig, finite-face contact equations, geometry
snapshots and a reproducible CAD motion/collision study.

- [Stage 3A: rig, animation, contact solution and next gates](docs/contact-rig.md)
- [Numerical and CAD evidence](docs/contact-proof.json)
- [Verification record and known limits](docs/verification.md)
- [Earlier drive comparison](docs/drive-comparison.md)

The rig develops the mechanism before the decorated terrace. Physical fit,
friction, noise, retention and endurance remain open; this is not a production
release or a ready-to-slice test plate.

## Files

| Path | Contents |
|---|---|
| `docs/brief.md` | Client brief, verbatim; source of truth |
| `docs/look-brief.md` | Research, references, palette and original concepts; the client subsequently chose Nikisz |
| `docs/design-notes.md` | Historical engineering starting points |
| `docs/drive-comparison.md` | Approved drive direction and screening limitations |
| `docs/contact-rig.md` | Current contact engineering, evidence and staged acceptance gates |
| `docs/verification.md` | Completed checks and existing repository lint issues |
| `src/fala/model.py` | Parametric rig geometry, validated dimensions and rigid poses |
| `engineering/prove_contact.py` | Contact/collision evidence; calls shared export/render tools |
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
uv run python projects/fala/engineering/prove_contact.py --export --render
```

The last command checks signed full rotations at 1° intervals, regenerates the
evidence, exports the rig, renders its actual CAD and saves a forward/reverse
animation. Exports stay under `projects/fala/dist/fala/0.1.0/contact_rig/`.
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

Next, resolve test-rig axis retention and print orientation, then issue a U1 fit
ladder and representative loaded test. Broad upper contacts seat geometrically;
the roughly 0.33–0.50 mm return clearance is not a measurement of free rocking or
real print fit. The pin and keel are centred in their clearances during the study.

The full terrace still needs concealed joints, roof clearance, transmission and
overload design. Keep the provisional 3:1 ratio explicitly unconfirmed. Lettering,
rear panel, ballast and filament brand remain open and need not block rig work.

All Fala materials stay in this project directory. Reusable mechanics and
plumbing belong in `cadkit`. Third-party research photos must stay out of shipped
or published material; see `research/SOURCES.md`. Commit only when requested.
