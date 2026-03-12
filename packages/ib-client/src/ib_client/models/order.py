from __future__ import annotations

from pydantic import Field, model_validator

from ib_client.models.base import IBModel


class OrderRequest(IBModel):
    account_id: str = Field(alias="acctId")
    conid: str
    side: str
    quantity: float
    order_type: str = Field(alias="orderType")
    tif: str = "DAY"
    price: float | None = None
    outside_rth: bool = Field(default=False, alias="outsideRTH")

    @model_validator(mode="after")
    def validate_price_requirement(self) -> OrderRequest:
        if self.order_type in {"LMT", "STP", "STP_LMT"} and self.price is None:
            raise ValueError("price is required for this order type")
        return self

    def to_payload(self) -> dict[str, list[dict[str, object]]]:
        order_payload: dict[str, object] = {
            "acctId": self.account_id,
            "conid": self.conid,
            "side": self.side,
            "quantity": self.quantity,
            "orderType": self.order_type,
            "tif": self.tif,
            "outsideRTH": self.outside_rth,
        }
        if self.price is not None:
            order_payload["price"] = self.price
        return {"orders": [order_payload]}


class OrderResponseItem(IBModel):
    order_id: str | int | None = Field(default=None, alias="order_id")
    id: str | None = None
    message: str | list[str] | None = None
    warning_message: str | None = Field(default=None, alias="warning_message")
    reply_id: str | None = Field(default=None, alias="id")


class LiveOrdersResponse(IBModel):
    orders: list[dict[str, object]] = Field(default_factory=list)
    snapshot: bool | None = None


class OrderResponseEnvelope(IBModel):
    items: list[OrderResponseItem] = Field(default_factory=list)
