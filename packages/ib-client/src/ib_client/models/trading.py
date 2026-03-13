from __future__ import annotations

from pydantic import Field

from ib_client.models.base import IBModel


class OrderStatus(IBModel):
    order_id: int | str | None = Field(default=None, alias="orderId")
    status: str | None = None
    filled: float | str | None = None
    remaining: float | str | None = None
    avg_fill_price: float | str | None = Field(default=None, alias="avgFillPrice")
    order_desc: str | None = Field(default=None, alias="orderDesc")


class Trade(IBModel):
    execution_id: str | None = Field(default=None, alias="executionId")
    symbol: str | None = None
    side: str | None = None
    quantity: float | str | None = Field(default=None, alias="qty")
    price: float | str | None = None
    conid: int | str | None = None
    trade_time: str | int | None = Field(default=None, alias="tradeTime")
    order_ref: str | None = Field(default=None, alias="order_ref")


class ScannerParameters(IBModel):
    instrument_list: list[dict[str, object]] = Field(default_factory=list, alias="instrument_list")
    scan_type_list: list[dict[str, object]] = Field(default_factory=list, alias="scan_type_list")
    location_tree: list[dict[str, object]] = Field(default_factory=list, alias="location_tree")
    filter_list: list[dict[str, object]] = Field(default_factory=list, alias="filter_list")


class ScannerResult(IBModel):
    symbol: str | None = None
    conid: int | str | None = None
    description: str | None = None
    scan_data: str | None = Field(default=None, alias="scan_data")
    company_name: str | None = Field(default=None, alias="company_name")
    contract_description_1: str | None = Field(default=None, alias="contract_description_1")
    listing_exchange: str | None = Field(default=None, alias="listing_exchange")
    sec_type: str | None = Field(default=None, alias="sec_type")


class Watchlist(IBModel):
    id: str | int | None = None
    name: str | None = None
    read_only: bool | None = Field(default=None, alias="readOnly")
    rows: list[dict[str, object]] = Field(default_factory=list)
