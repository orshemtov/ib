from __future__ import annotations

from pydantic import Field

from ib_client.models.base import IBModel


class ContractSearchResult(IBModel):
    conid: int | str | None = None
    company_name: str | None = Field(default=None, alias="companyName")
    description: str | None = None
    symbol: str | None = None
    listing_exchange: str | None = Field(default=None, alias="listingExchange")
    sec_type: str | None = Field(default=None, alias="secType")


class MarketSnapshot(IBModel):
    conid: int | str | None = None
    symbol: str | None = Field(default=None, alias="55")
    last_price: float | str | None = Field(default=None, alias="31")
    bid_price: float | str | None = Field(default=None, alias="84")
    ask_price: float | str | None = Field(default=None, alias="86")
