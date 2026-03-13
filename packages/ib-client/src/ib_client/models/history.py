from __future__ import annotations

from pydantic import Field

from ib_client.models.base import IBModel


class HistoricalBar(IBModel):
    open: float | None = Field(default=None, alias="o")
    high: float | None = Field(default=None, alias="h")
    low: float | None = Field(default=None, alias="l")
    close: float | None = Field(default=None, alias="c")
    volume: float | None = Field(default=None, alias="v")
    timestamp: int | str | None = Field(default=None, alias="t")


class HistoricalDataResponse(IBModel):
    server_id: str | None = Field(default=None, alias="serverId")
    symbol: str | None = None
    text: str | None = None
    price_factor: float | None = Field(default=None, alias="priceFactor")
    md_availability: str | None = Field(default=None, alias="mdAvailability")
    points: int | None = None
    data: list[HistoricalBar] = Field(default_factory=list)
