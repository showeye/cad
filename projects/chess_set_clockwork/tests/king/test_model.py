"""The king builds, passes the workspace quality gate and matches its snapshot."""

from pathlib import Path

from cadkit.testing import check_model
from chess_set_clockwork.king.model import model


def test_variants():
    # the knight's variant has the same name, so the king's snapshot has its own folder
    check_model(model, Path(__file__).with_name("snapshots"))
