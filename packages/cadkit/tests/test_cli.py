"""All-variant builds must support products whose SKUs do not include 'full'."""

import sys

from cadkit import cli
from cadkit.model import Model
from cadkit.params import Params
from cadkit.process import FDM


def test_all_variants_without_full(monkeypatch, tmp_path):
    model = Model("sample", "0.1.0", {"closed": Params(), "open": Params()}, FDM, lambda _: {})
    exported = []

    def export(chosen, variant):
        assert chosen is model
        exported.append(variant)
        return tmp_path / variant

    monkeypatch.setattr(cli, "discover", lambda: {"sample": model})
    monkeypatch.setattr(cli, "export_model", export)
    monkeypatch.setattr(sys, "argv", ["cadkit", "build", "sample", "--all"])
    cli.main()
    assert exported == ["closed", "open"]
