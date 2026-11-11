"""Reproducible engraving tools using the bundled SIL OFL Barlow Condensed typeface."""

from importlib.resources import files

from build123d import Text, extrude


def engraving(text: str, size: float, depth: float = 0.8):
    """Text cutting tool at z=0 pointing -Z; position with Pos/Plane before subtraction."""
    if not text.strip() or min(size, depth) <= 0:
        raise ValueError("Engraving needs text, a positive size and a positive depth")
    font = files("cadkit").joinpath("assets/BarlowCondensed-SemiBold.ttf")
    return extrude(Text(text, font_size=size, font_path=str(font)), amount=-depth)
