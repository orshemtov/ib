from __future__ import annotations

from typing import Any

from pydantic import AliasChoices, Field, field_validator

from ib_client.models.base import IBModel


class Account(IBModel):
    id: str | None = None
    account_id: str | None = Field(default=None, alias="accountId")
    account_title: str | None = Field(default=None, alias="accountTitle")
    account_status: int | None = Field(default=None, alias="accountStatus")
    currency: str | None = None
    type: str | None = None
    business_type: str | None = Field(default=None, alias="businessType")

    @property
    def identifier(self) -> str | None:
        return self.account_id or self.id


class AccountSummary(IBModel):
    account_id: str | None = Field(default=None, alias="accountId")
    account_type: str | None = Field(default=None, alias="accountType")
    currency: str | None = None
    net_liquidation: float | str | None = Field(
        default=None,
        validation_alias=AliasChoices("netliquidation", "netLiquidation"),
    )
    total_cash_value: float | str | None = Field(
        default=None,
        validation_alias=AliasChoices("totalcashvalue", "totalCashValue"),
    )

    @field_validator("net_liquidation", "total_cash_value", mode="before")
    @classmethod
    def extract_amount(cls, value: Any) -> Any:
        if isinstance(value, dict) and "amount" in value:
            return value["amount"]
        return value


class Position(IBModel):
    account_id: str | None = Field(default=None, alias="acctId")
    conid: int | str | None = None
    contract_desc: str | None = Field(default=None, alias="contractDesc")
    position: float | None = None
    market_price: float | None = Field(default=None, alias="mktPrice")
    market_value: float | None = Field(default=None, alias="mktValue")
    currency: str | None = None


class ProfitAndLoss(IBModel):
    account_id: str | None = Field(default=None, alias="acctId")
    daily: float | None = Field(default=None, alias="dpl")
    unrealized: float | None = Field(default=None, alias="upl")
    realized: float | None = Field(default=None, alias="rpl")
