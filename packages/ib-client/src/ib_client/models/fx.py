from __future__ import annotations

from pydantic import Field, field_validator, model_validator

from ib_client.models.base import IBModel


class CurrencyPair(IBModel):
    requested_currency: str | None = None
    symbol: str | None = None
    conid: int | str | None = None
    counter_currency: str | None = Field(default=None, alias="ccyPair")


class ResolvedCurrencyPair(IBModel):
    source_currency: str
    target_currency: str
    symbol: str
    conid: int | str
    is_inverse: bool = False


class ExchangeRate(IBModel):
    source_currency: str
    target_currency: str
    rate: float | None = None


class FXConversionRequest(IBModel):
    account_id: str = Field(alias="acctId")
    conid: int | str | None = None
    conidex: str | None = None
    side: str
    fx_quantity: float = Field(alias="fxQty")
    order_type: str = Field(default="MKT", alias="orderType")
    tif: str = "DAY"
    price: float | None = None
    outside_rth: bool = Field(default=False, alias="outsideRTH")
    is_currency_conversion: bool = Field(default=True, alias="isCcyConv")

    @field_validator("side", "order_type", "tif", mode="before")
    @classmethod
    def normalize_uppercase_fields(cls, value: str) -> str:
        return value.upper()

    @model_validator(mode="after")
    def validate_request(self) -> FXConversionRequest:
        if (self.conid is None) == (self.conidex is None):
            raise ValueError("exactly one of conid or conidex is required")
        if self.fx_quantity <= 0:
            raise ValueError("fxQty must be greater than zero")
        if self.order_type in {"LMT", "STP", "STP_LMT", "STOP_LIMIT"} and self.price is None:
            raise ValueError("price is required for this order type")
        return self

    def to_payload(self) -> dict[str, list[dict[str, object]]]:
        order_payload: dict[str, object] = {
            "acctId": self.account_id,
            "side": self.side,
            "fxQty": self.fx_quantity,
            "orderType": self.order_type,
            "tif": self.tif,
            "outsideRTH": self.outside_rth,
            "isCcyConv": self.is_currency_conversion,
        }
        if self.conid is not None:
            order_payload["conid"] = self.conid
        if self.conidex is not None:
            order_payload["conidex"] = self.conidex
        if self.price is not None:
            order_payload["price"] = self.price
        return {"orders": [order_payload]}


class FXCloseToUSDPlan(IBModel):
    account_id: str
    currency: str
    cash_balance: float
    source_currency: str
    target_currency: str = "USD"
    pair_symbol: str
    pair_conid: int | str
    side: str
    fx_quantity: float
    estimated_rate: float | None = None
    request: FXConversionRequest


class FXCloseToUSDPreview(IBModel):
    plan: FXCloseToUSDPlan
    preview: dict[str, object]


class FXCloseToUSDPlacement(IBModel):
    plan: FXCloseToUSDPlan
    placed: dict[str, object]
