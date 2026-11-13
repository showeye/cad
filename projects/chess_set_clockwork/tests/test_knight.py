"""The knight builds, passes the workspace quality gate and matches its snapshot."""

from pathlib import Path

from cadkit.testing import check_model
from chess_set_clockwork.knight import model


def test_variants():
    check_model(model, Path(__file__).with_name("snapshots"))
