"""Every motion-prototype variant passes the workspace's BRep/mesh/snapshot gate."""

from pathlib import Path

from cadkit.testing import check_model
from serce.coupons import model as coupons
from serce.model import model


def test_variants():
    check_model(model, Path(__file__).parent / "snapshots")


def test_coupon_variants():
    check_model(coupons, Path(__file__).parent / "snapshots" / "coupons")
