"""Packaging of rendered frames into films; the Blender process itself is not run here."""

from cadkit.render import clear_frames, finish_presentation
from PIL import Image


def _frames(folder, count):
    folder.mkdir()
    for i in range(count):
        Image.new("RGB", (8, 6), (i * 40, 0, 0)).save(folder / f"{i:03}.png")


def test_every_film_becomes_its_own_gif(tmp_path):
    _frames(tmp_path / "frames", 5)
    _frames(tmp_path / "frames_bare", 5)
    spec = {
        "animation": {"loop": True, "frame_ms": 80},
        "films": {"bare": {"frame_ms": 120}},
    }
    finish_presentation(tmp_path, "thing", "1.0.0", animate=True, spec=spec)
    with Image.open(tmp_path / "motion.gif") as film:
        assert film.n_frames == 4  # a looping film drops its last pose: it repeats the first
        assert film.info["duration"] == 80
    with Image.open(tmp_path / "bare.gif") as film:
        assert film.n_frames == 5 and film.info["duration"] == 120
    assert (tmp_path / "concept-sheet.jpg").exists()


def test_no_film_without_frames_or_when_not_asked(tmp_path):
    finish_presentation(tmp_path, "thing", "1.0.0", animate=True, spec={"films": {"bare": {}}})
    assert not list(tmp_path.glob("*.gif"))
    _frames(tmp_path / "frames", 3)
    finish_presentation(tmp_path, "thing", "1.0.0", animate=False)
    assert not list(tmp_path.glob("*.gif"))


def test_frames_of_an_earlier_render_are_cleared(tmp_path):
    _frames(tmp_path / "frames", 5)
    _frames(tmp_path / "frames_bare", 3)
    still = tmp_path / "hero.png"
    still.write_bytes(b"kept")
    clear_frames(tmp_path)
    assert not list(tmp_path.glob("frames*/*.png"))
    assert still.read_bytes() == b"kept"  # stills are not frames
