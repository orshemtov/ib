from __future__ import annotations

from pydantic import Field

from ib_client.models.base import IBModel


class StockLookupContract(IBModel):
    conid: int | str | None = None
    symbol: str | None = None
    exchange: str | None = None
    name: str | None = None
    asset_class: str | None = Field(default=None, alias="assetClass")
    chinese_name: str | None = Field(default=None, alias="chineseName")
    contracts: list[dict[str, object]] = Field(default_factory=list)


class SecurityDefinition(IBModel):
    conid: int | str | None = None
    symbol: str | None = None
    exchange: str | None = None
    listing_exchange: str | None = Field(default=None, alias="listingExchange")
    sec_type: str | None = Field(default=None, alias="secType")
    currency: str | None = None
    description: str | None = None


class OptionStrikes(IBModel):
    call: list[float | str] = Field(default_factory=list)
    put: list[float | str] = Field(default_factory=list)
    month: str | None = None
    multiplier: str | None = None


class OptionContract(IBModel):
    conid: int | str | None = None
    symbol: str | None = None
    description: str | None = None
    exchange: str | None = None
    strike: float | str | None = None
    right: str | None = None
    maturity_date: str | None = Field(default=None, alias="maturityDate")
    trading_class: str | None = Field(default=None, alias="tradingClass")
    multiplier: str | None = None


class ContractRule(IBModel):
    conid: int | str | None = None
    exchange: str | None = None
    order_types: list[str] | str | None = Field(default=None, alias="orderTypes")
    default_size: float | str | None = Field(default=None, alias="defaultSize")
    size_increment: float | str | None = Field(default=None, alias="sizeIncrement")
    price_increment: float | str | None = Field(default=None, alias="priceIncrement")
    increment_rules: list[dict[str, object]] = Field(default_factory=list, alias="incrementRules")
