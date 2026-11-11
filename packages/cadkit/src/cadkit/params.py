"""Immutable, validated model parameters; all lengths in mm and angles in degrees."""

from pydantic import BaseModel, ConfigDict


class Params(BaseModel):
    """Base for product parameters; reject unknown fields and mutation."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)
