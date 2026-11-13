# Clockwork chess set

A 3D-printed chess set in the style of skeleton clocks, where each piece holds clockwork parts
that do something. Everything for this product lives in this folder.

## Status (2026-11-13, first discussion)

**Concept only. Nothing is modelled, and this folder is not a `cadkit` package yet.**

- The client supplied one concept picture and asked whether the pieces can hold movement that
  does anything meaningful.
- The assessment is in `docs/brief.md`: real clockwork parts driven by handling will work; a
  movement that runs by itself will not. The recommended concept is "one tick per move".
- The client asked for the assessment to be stored as the brief for future work. The three
  decisions in section 6 of the brief are not answered.

## How to continue

1. Read `docs/brief.md`.
2. Get the client's answers to its section 6: hardware, size, and files or printed sets.
3. Start with the pawn, the tightest fit (section 8 of the brief). Set the package up like
   `projects/fala` (a `pyproject.toml` that registers the `cadkit.models` entry point) and add
   it to the workspace members in the root `pyproject.toml`. `cadkit new` does not exist yet.

## Where things are

| Path | What it is |
|---|---|
| `docs/brief.md` | The idea, the verdict, the recommended concept, open decisions and how the estimates were made |
| `A_skeleton_clocks.png` | The client's concept picture: style reference only, its mechanisms do not work as drawn |
