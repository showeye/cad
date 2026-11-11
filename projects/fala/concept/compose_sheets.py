"""Fala concept checkpoint: compose the look comparison sheet and the wave filmstrips.

Needs the PNGs written by look_concepts.py --strip (the strip_*.png frames are deleted
again once the filmstrips are composed).

    uv run python projects/fala/concept/look_concepts.py --no-show --strip
    uv run python projects/fala/concept/compose_sheets.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

IMG = Path(__file__).resolve().parents[1] / "docs" / "img"
BG = (243, 240, 234)


def font(size):
    for name in (
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def crop(im, box):
    w, h = im.size
    return im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))


labels = {
    "nikisz": "LOOK 1  NIKISZ   stepped bays, gateway + oriel, dark brick",
    "kolonia": "LOOK 2  KOLONIA   one repeated familok, arched red windows",
    "bajka": "LOOK 3  BAJKA   storybook: fat, uneven, oversized",
}
rows = []
for look, label in labels.items():
    front = crop(
        Image.open(IMG / f"look_{look}_front_rest.png").convert("RGB"), (0.05, 0.14, 0.95, 0.86)
    )
    hero = crop(
        Image.open(IMG / f"look_{look}_hero_wave.png").convert("RGB"), (0.08, 0.03, 0.98, 0.99)
    )
    h = 520
    front = front.resize((int(front.width * h / front.height), h), Image.LANCZOS)
    hero = hero.resize((int(hero.width * h / hero.height), h), Image.LANCZOS)
    row = Image.new("RGB", (front.width + hero.width + 30, h + 58), BG)
    row.paste(front, (0, 58))
    row.paste(hero, (front.width + 30, 58))
    d = ImageDraw.Draw(row)
    d.text((24, 14), label, fill=(38, 38, 42), font=font(30))
    d.text((front.width + 54, 22), "posed on the wave", fill=(120, 116, 108), font=font(20))
    rows.append(row)
W = max(r.width for r in rows)
sheet = Image.new("RGB", (W, sum(r.height for r in rows) + 20), BG)
y = 0
for r in rows:
    sheet.paste(r, (0, y))
    y += r.height + 10
sheet.save(IMG / "looks_comparison.png")
print("looks_comparison", sheet.size)

for look in labels:
    frames = [
        crop(
            Image.open(IMG / f"strip_{look}_{ph:03d}.png").convert("RGB"), (0.06, 0.05, 0.94, 0.80)
        )
        for ph in (0, 90, 180, 270)
    ]
    fw, fh = frames[0].size
    s = 0.62
    frames = [f.resize((int(fw * s), int(fh * s)), Image.LANCZOS) for f in frames]
    fw, fh = frames[0].size
    strip = Image.new("RGB", (fw * 2 + 20, fh * 2 + 20), BG)
    for i, f in enumerate(frames):
        strip.paste(f, ((i % 2) * (fw + 20), (i // 2) * (fh + 20)))
        ImageDraw.Draw(strip).text(
            ((i % 2) * (fw + 20) + 18, (i // 2) * (fh + 20) + 12),
            f"crank phase {i * 90} deg",
            fill=(120, 116, 108),
            font=font(20),
        )
    strip.save(IMG / f"wave_strip_{look}.png")
    print("strip", look, strip.size)

for frame in IMG.glob("strip_*.png"):
    frame.unlink()
