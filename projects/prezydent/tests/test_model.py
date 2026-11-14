"""All SKUs pass the shared BRep/mesh and snapshot gate; the scale claims hold."""

from pathlib import Path

from cadkit.testing import check_model
from cadkit.validate import overlaps
from prezydent.model import Params, build, fidelity, model


def test_variants():
    check_model(model, Path(__file__).parent / "snapshots")


def test_parts_do_not_intersect():
    assert not overlaps(build(model.variants["s250"]))


def test_concrete_is_true_to_scale_at_250():
    rows = fidelity(model.variants["s250"])
    concrete = [r for r in rows if r["group"] == "concrete"]
    assert concrete and all(r["printed"] == r["true"] for r in concrete)
    assert any(r["printed"] > r["true"] for r in rows if r["group"] == "fittings")


def test_smaller_scale_thickens_the_beams():
    rows = {r["member"]: r for r in fidelity(Params(scale=350))}
    assert rows["tie beam, width"]["printed"] > rows["tie beam, width"]["true"]


def test_height_follows_the_scale():
    params = model.variants["s250"]
    top = build(params)["concrete"].bounding_box().max.Z
    assert abs(top - params.tower.deck_z * 1000 / params.scale) < 1e-6
