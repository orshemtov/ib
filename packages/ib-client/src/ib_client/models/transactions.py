from __future__ import annotations

from pydantic import Field, model_validator

from ib_client.models.base import IBModel


class TransactionHistoryRequest(IBModel):
    account_ids: list[str] = Field(alias="acctIds")
    conids: list[int | str]
    currency: str = "USD"
    days: int | None = None

    @model_validator(mode="after")
    def validate_single_conid(self) -> TransactionHistoryRequest:
        if len(self.conids) != 1:
            raise ValueError("exactly one conid is required")
        return self

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "acctIds": self.account_ids,
            "conids": self.conids,
            "currency": self.currency,
        }
        if self.days is not None:
            payload["days"] = self.days
        return payload


class RealizedPnLRow(IBModel):
    date: str | None = None
    currency: str | None = Field(default=None, alias="cur")
    fx_rate: float | int | None = Field(default=None, alias="fxRate")
    side: str | None = None
    account_id: str | None = Field(default=None, alias="acctid")
    amount: float | str | None = Field(default=None, alias="amt")
    conid: int | str | None = None


class RealizedPnLSummary(IBModel):
    data: list[RealizedPnLRow] = Field(default_factory=list)
    amount: float | str | None = Field(default=None, alias="amt")


class TransactionRecord(IBModel):
    date: str | None = None
    currency: str | None = Field(default=None, alias="cur")
    fx_rate: float | int | None = Field(default=None, alias="fxRate")
    price: float | None = Field(default=None, alias="pr")
    quantity: float | int | None = Field(default=None, alias="qty")
    account_id: str | None = Field(default=None, alias="acctid")
    amount: float | str | None = Field(default=None, alias="amt")
    conid: int | str | None = None
    type: str | None = None
    description: str | None = Field(default=None, alias="desc")


class TransactionHistoryResponse(IBModel):
    return_code: int | None = Field(default=None, alias="rc")
    day_count: int | None = Field(default=None, alias="nd")
    realized_pnl: RealizedPnLSummary | None = Field(default=None, alias="rpnl")
    currency: str | None = None
    from_timestamp: int | None = Field(default=None, alias="from")
    request_id: str | None = Field(default=None, alias="id")
    to_timestamp: int | None = Field(default=None, alias="to")
    includes_real_time: bool | None = Field(default=None, alias="includesRealTime")
    transactions: list[TransactionRecord] = Field(default_factory=list)
