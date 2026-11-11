"""Product model contract and installed entry-point discovery."""

from collections.abc import Callable
from dataclasses import dataclass
from importlib.metadata import entry_points

from build123d import Shape

from cadkit.params import Params
from cadkit.process import Process


@dataclass(frozen=True)
class Model:
    """Public model contract; build returns individually named, single-solid parts."""

    name: str
    version: str
    variants: dict[str, Params]
    process: Process
    build: Callable[[Params], Shape | dict[str, Shape]]


def discover() -> dict[str, Model]:
    """Load workspace products registered under cadkit.models."""
    return {ep.name: ep.load() for ep in entry_points(group="cadkit.models")}
