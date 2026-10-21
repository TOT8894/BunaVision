from typing import Literal

from pydantic import BaseModel, ConfigDict


class HealthOut(BaseModel):
    """Liveness only. Deliberately exposes no configuration or dependency details."""

    model_config = ConfigDict(frozen=True)

    status: Literal["ok"]
    version: str
