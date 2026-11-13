"""Nominal hardware envelopes around Z, not manufactured threads or strength models.

Head bearing planes are z=0; screws point -Z, like cutting tools. Sources:
ISO 4762 (M3 socket screw), ISO 4032 (M3 hex nut), DIN 705 (4 mm collar).
The 4-M3 shoulder screw is an Elesa+Ganter extension of ISO 7379, NOT a size
in the official standard. Verify against datasheet before buying:
https://live-katalog.ganternorm.com/pdf/ganter/en/7379.pdf
Collar dimensions: https://gardette.com/en/catalog/shaft-collars-din-705
"""

from build123d import Cylinder, Pos

from cadkit.features.mechanical import hex_prism


def shoulder_screw_4_m3(length: float = 12):
    """Vendor 4 mm shoulder/M3 screw: 7×3 head, 7 mm thread; verify datasheet."""
    if length not in (4, 5, 6, 8, 10, 12, 16, 20, 25, 30):
        raise ValueError("Unsupported vendor shoulder length")
    shape = Pos(0, 0, 1.5) * Cylinder(3.5, 3)
    shape += Pos(0, 0, -length / 2) * Cylinder(2, length)
    return shape + Pos(0, 0, -length - 3.5) * Cylinder(1.5, 7)


def socket_screw_m3(length: float = 8):
    """ISO 4762 M3 nominal envelope, 5.5 mm head diameter and 3 mm head height."""
    if length <= 0:
        raise ValueError("Positive screw length required")
    return Pos(0, 0, 1.5) * Cylinder(2.75, 3) + Pos(0, 0, -length / 2) * Cylinder(1.5, length)


def nut_m3(height: float = 2.4):
    """ISO 4032 M3, 5.5 mm flats; optional height for a vendor locknut envelope.

    A nonstandard height does not assert ISO 4032 conformity. For locknuts,
    verify the purchased part's total height and nylon engagement separately.
    """
    if height <= 0:
        raise ValueError("Positive nut height required")
    return hex_prism(5.5 / 3**0.5, height) - Cylinder(1.5, height + 2)


def shaft_collar_4():
    """DIN 705 4 mm bore, 8 mm OD, 5 mm width; set screw included in envelope."""
    return Cylinder(4, 5) - Cylinder(2, 7)
