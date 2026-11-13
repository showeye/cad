"""Manufacturing profiles with explicit prototype fits and mesh quality in mm."""

from pydantic import Field

from cadkit.params import Params


class Process(Params):
    """Build volume applies to each part; fit is a diametral initial allowance."""

    name: str = "FDM prototype, 0.4 mm nozzle"
    build_volume: tuple[float, float, float] = (220, 220, 250)
    fit: float = Field(default=0.4, ge=0.1, le=1)
    mesh_tolerance: float = Field(default=0.04, gt=0, le=0.2)


FDM = Process()

# Snapmaker U1: FDM toolchanger, four toolheads, 0.4 mm nozzle (maker's specification sheet).
U1 = Process(name="Snapmaker U1, FDM, 0.4 mm nozzle, 4 colours", build_volume=(270, 270, 270))
