from __future__ import annotations

from pydantic import Field

from ib_client.models.base import IBModel


class LedgerEntry(IBModel):
    currency: str | None = None
    cash_balance: float | str | None = Field(default=None, alias="cashbalance")
    stock_market_value: float | str | None = Field(default=None, alias="stockmarketvalue")
    net_liquidation_value: float | str | None = Field(default=None, alias="netliquidationvalue")
    buying_power: float | str | None = Field(default=None, alias="buyingpower")


class ComboPosition(IBModel):
    conid: int | str | None = None
    description: str | None = None
    position: float | None = None
    market_price: float | None = Field(default=None, alias="marketPrice")
    market_value: float | None = Field(default=None, alias="marketValue")
    currency: str | None = None
