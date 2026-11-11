# Na szychcie od 1915 — Carnall

Full-form engineering concept, version 0.1.0. Overall size: 180 × 90 × 120 mm.

![CAD concept](hero.png)

Open [concept-sheet.jpg](concept-sheet.jpg) for the review sheet and [motion.gif](motion.gif)
for one crank revolution followed by its reverse. The model has two visible piston and
crosshead assemblies, swinging rods, a large rope wheel, a continuous cord loop and a driven
upper sheave. The cutaway architecture leaves the engine exposed.

- `assembly.step`: named CAD geometry, mm.
- `assembly.glb`: coloured 3D reference.
- `assembly.3mf`: coloured assembly reference, **not a prepared print plate**.
- `parts/`: 47 individual component STLs in assembly coordinates; orient before slicing.
- `presentation.blend`: animated Blender scene; play frames 1–97.
- `manifest.json`: parameters, metrics, library versions, git status, source and artifact hashes.
- [docs/research.md](docs/research.md): historical references, design rationale and copy.
- [docs/engineering.md](docs/engineering.md): motion, assembly, hardware and prototype plan.
- [docs/verification.md](docs/verification.md): completed checks and their limits.

The cream cord and its small witness marker are references, excluded from printable parts.
Use purchased flexible cord. The piston stroke is 16 mm; the sheave turns about 2.695 times
per main-wheel revolution. The actual engine is a Koepe friction-wheel machine; the cord
travels continuously rather than accumulating on a drum.

This is a stylised interpretation, not a measured replica. Quartering, arches and proportions
are design choices. The heritage card line is “2,000 KM. On shift since 1915.” The optional
joke belongs on the card: “On shift since 1915. Still no pension.”

**Physical prototype required:** confirm running fits, cord grip, pin and axle retention,
shaft strength and endurance before sale. Some retention hardware still needs selection;
see the engineering notes. Source models and the shared cadkit package are in the CAD repository.
