"""Standard variant quality gate and explicit opt-in geometry snapshot regeneration."""

import json
import os
from pathlib import Path

from cadkit.model import Model
from cadkit.validate import metrics, parts_of, validate


def check_model(model: Model, snapshots: Path):
    """Build every SKU, validate and compare its complete per-part snapshot."""
    for variant, params in model.variants.items():
        parts = parts_of(model.build(params))
        assert not (errors := validate(parts, model.process)), "\n".join(errors)
        actual = {"version": model.version, "parts": {k: metrics(v) for k, v in parts.items()}}
        target = snapshots / f"{variant}.json"
        if os.environ.get("CADKIT_UPDATE_SNAPSHOTS") == "1":
            snapshots.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(actual, indent=2, sort_keys=True) + "\n")
        assert target.exists(), f"Missing snapshot {target}; explicitly initialise it"
        assert json.loads(target.read_text()) == actual, f"Geometry changed for {variant}"
