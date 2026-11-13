# Stage 3A verification — 2026-11-13

Model: `fala` 0.1.0, variant `contact_rig`. Verification ran against repository
base `1a4cbff` plus the stage 3A implementation, before its checkpoint commit.
This is not a production release. Exact source hashes accompany the evidence
and export manifest.

## Checks completed

| Check | Result |
|---|---|
| `uv sync --all-packages` | Fala installed as a workspace package |
| Full workspace `uv run pytest -q` | **105 passed**; 112.88 seconds in the final run |
| Shared variant gate | Seven single-solid valid BReps; closed oriented meshes; all within U1 volume |
| Fala geometry snapshot | `tests/snapshots/contact_rig.json` matches 0.1.0 |
| Existing product snapshots | Carnall unchanged; full workspace suite passes |
| Finite-contact equations | Surface/plane coincidence, concentric limit, signed phases, finite lower-face projection and negative-gap detection tested |
| CAD collision/contact study | 360 positive + 360 negative phases at 1°; no intersection above `1e-5 mm³` |
| Upper follower contact | Worst cam-to-carriage separation below `0.000001 mm` in the sampled CAD poses |
| Adjacent carriage separation | Minimum approximately **1.855 mm** in the sampled poses |
| Frame separation | Minimum approximately **0.200 mm** to both cam and carriages |
| Assembly path | Axial threading and lowering of the cam/carriage group checked at 2 mm intervals |
| Rigid render transforms | Agree with independently built CAD poses; rotations remain rigid and reverse poses agree |
| Export reproducibility | All seven CAD file hashes match across independent processes and contact-check histories |
| CAD presentation | Five views, forward/backward animation and a Blender scene rendered from the actual tessellation |
| VS Code review | Rig sent to the existing OCP CAD Viewer on port 3939 |
| `ruff check packages projects/fala` | Pass |
| `ruff format --check packages projects/fala` | Pass |
| `git diff --check` | Pass |

The per-phase counts, tolerances, measured extrema, parameters and source hashes
are in [contact-proof.json](contact-proof.json). CAD files and the Blender scene
are under `../dist/fala/0.1.0/contact_rig/`; `manifest.json` records their hashes.
The STEP timestamp is fixed by the shared exporter. The shared export tests also
check byte determinism across independent processes and reimport the outputs.

Fala's contact geometry exposed two shared reproducibility defects. The
intersection gate now requests non-destructive OCCT booleans so tangent contact
checks cannot raise the source topology's tolerances. The STEP normaliser now
also removes layout whitespace from occurrence records, preserving quoted names:
OCCT's process-wide numbering previously changed line wrapping even after IDs
were normalised. Regression checks cover both problems.

## Existing repository lint issues

Repository-wide `ruff check .` reports four existing findings under
`projects/serce/concept/`: import ordering in `heart_concept.py`, a preference for
`pairwise` in that file, and unused `noqa` directives in `look_concepts.py` and
`mechanism_diagrams.py`. Repository-wide formatting reports three Serce concept
files: `compose_sheets.py`, `heart_concept.py`, and `mechanism_diagrams.py`.
Those files were unchanged in this stage. All Cadkit and Fala files pass.

## What these checks do not establish

The sweep checks discrete centred CAD poses. It does not certify continuous
swept volumes, clearance-induced rocking, a loaded reversal, friction, starting
force, print fit, wear, noise or temperature resistance. The model omits final
axis retention and transmission. The exported 3MF is an assembly reference;
there is no released slicer plate, print-time measurement or physical test result.
See [the next-stage gates](contact-rig.md#next-stage-and-acceptance-gates).
