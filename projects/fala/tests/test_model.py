"""The contact development variant passes the workspace quality contract."""

from pathlib import Path

from cadkit.testing import check_model
from fala.model import model


def test_variants():
    check_model(model, Path(__file__).with_name("snapshots"))
