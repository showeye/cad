"""Serce na węgiel concept checkpoint: put the Blender renders on paper and build the sheets.

    uv run python projects/serce/concept/compose_sheets.py

Reads concept/_build/render/*.png (transparent film, shadow catcher) and writes docs/img/*.png.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
RENDER = HERE / "_build" / "render"
OUT = HERE.parent / "docs" / "img"
PAPER, INK, SOFT = "#F3F0EA", "#2B2B30", "#77736B"


def font(size, bold=False):
    for name in ("HelveticaNeue.ttc", "Helvetica.ttc", "Arial.ttf"):
        try:
            return ImageFont.truetype(f"/System/Library/Fonts/{name}", size, index=1 if bold else 0)
        except OSError:
            continue
    return ImageFont.load_default()


def on_paper(name, crop=None, width=None):
    """A render composited on the paper colour, optionally cropped (fractions) and resized."""
    image = Image.open(RENDER / f"{name}.png").convert("RGBA")
    flat = Image.new("RGBA", image.size, PAPER)
    flat.alpha_composite(image)
    flat = flat.convert("RGB")
    if crop:
        w, h = flat.size
        flat = flat.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
    if width:
        flat = flat.resize((width, round(flat.height * width / flat.width)), Image.LANCZOS)
    return flat


def sheet(rows, path, title=None, cell_gap=10, margin=28, caption_h=58):
    """rows: list of lists of (image, caption, sub-caption)."""
    widths = [sum(im.width for im, *_ in row) + cell_gap * (len(row) - 1) for row in rows]
    heights = [max(im.height for im, *_ in row) + caption_h for row in rows]
    top = 64 if title else margin
    canvas = Image.new("RGB", (max(widths) + 2 * margin, sum(heights) + top + margin), PAPER)
    draw = ImageDraw.Draw(canvas)
    if title:
        draw.text((margin, 22), title, fill=INK, font=font(26, bold=True))
    y = top
    for row, row_h in zip(rows, heights):
        x = margin
        for image, caption, sub in row:
            canvas.paste(image, (x, y))
            draw.text((x + 6, y + image.height + 6), caption, fill=INK, font=font(20, bold=True))
            if sub:
                draw.text((x + 6, y + image.height + 31), sub, fill=SOFT, font=font(16))
            x += image.width + cell_gap
        y += row_h
    canvas.save(path)
    print("wrote", path, canvas.size)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    hero = (0.14, 0.10, 0.86, 0.90)
    looks = [
        ("bryla", "1  Bryła (the lump)", "cleaved like real coal: big flat faces, small chips"),
        ("szlif", "2  Szlif (the cut)", "cut like a gemstone: table, crown facets, girdle"),
        ("poklad", "3  Pokład (the seam)", "banded like a coal seam: gloss and matte beds"),
    ]
    for key, *_ in looks:
        for state in ("closed", "open"):
            on_paper(f"look_{key}_{state}", hero).save(OUT / f"look_{key}_{state}.png")
    sheet(
        [
            [(on_paper(f"look_{k}_closed", hero, 600), cap, sub) for k, cap, sub in looks],
            [(on_paper(f"look_{k}_open", hero, 600), "open", "") for k, *_ in looks],
        ],
        OUT / "looks_comparison.png",
        "Three looks of the coal heart, closed and open",
    )
    square = (0.08, 0.08, 0.92, 0.92)
    turns = [
        "closed",
        "40° turn: first light",
        "80°: the bud",
        "120°: the room",
        "180°: fully open",
    ]
    sheet(
        [[(on_paper(f"wings_{i}", square, 400), t, "") for i, t in enumerate(turns)]],
        OUT / "opening_a_wings_strip.png",
        "A  Skrzydła: half a turn of the base",
        caption_h=40,
    )
    steps = ["closed", "a seam of light", "the curtain rises", "fully open"]
    sheet(
        [[(on_paper(f"lift_{i}", square, 400), t, "") for i, t in enumerate(steps)]],
        OUT / "opening_b_seam_lift_strip.png",
        "B  Pokład: the top rises 30 mm",
        caption_h=40,
    )
    steps = ["closed", "four cracks", "the shards tip out", "fully open, room raised"]
    sheet(
        [[(on_paper(f"bloom_{i}", square, 400), t, "") for i, t in enumerate(steps)]],
        OUT / "opening_c_bloom_strip.png",
        "C  Rozkwit: four shards and a rising room",
        caption_h=40,
    )
    sheet(
        [
            [
                (
                    on_paper("wings_counter", square, 520),
                    "A  Skrzydła",
                    "the whole room is in view",
                ),
                (
                    on_paper("lift_counter", square, 520),
                    "B  Pokład",
                    "the raised top hides the room",
                ),
                (
                    on_paper("bloom_counter", square, 520),
                    "C  Rozkwit",
                    "open all round, 190 mm wide",
                ),
            ]
        ],
        OUT / "counter_view_comparison.png",
        "Seen from above, as on a shop counter (42° down)",
    )
    sheet(
        [
            [
                (
                    on_paper("look_bryla_open", hero, 700),
                    "Honey lining (recommended)",
                    "the shell glows like a lit window",
                ),
                (
                    on_paper("wings_open_ember", hero, 700),
                    "Tile-red lining",
                    "the shell glows like embers; the room stands out more",
                ),
            ]
        ],
        OUT / "lining_comparison.png",
        "Lining of the shell: two options from the same four filaments",
    )
    on_paper("wings_back", square, 700).save(OUT / "wings_back_closed.png")
