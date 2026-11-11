"""All SKUs pass the shared BRep/mesh and snapshot gate."""

from pathlib import Path

from cadkit.testing import check_model
from carnall.model import model


def test_variants():
    check_model(model, Path(__file__).parent / "snapshots")
