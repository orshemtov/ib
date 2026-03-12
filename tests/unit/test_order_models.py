import pytest
from ib_client.models.order import OrderRequest


def test_market_order_payload_omits_price() -> None:
    order = OrderRequest.model_validate(
        {
            "acctId": "DU123456",
            "conid": "265598",
            "side": "BUY",
            "quantity": 1,
            "orderType": "MKT",
            "tif": "DAY",
        }
    )

    assert order.to_payload() == {
        "orders": [
            {
                "acctId": "DU123456",
                "conid": "265598",
                "side": "BUY",
                "quantity": 1.0,
                "orderType": "MKT",
                "tif": "DAY",
                "outsideRTH": False,
            }
        ]
    }


def test_limit_order_requires_price() -> None:
    with pytest.raises(ValueError, match="price is required"):
        OrderRequest.model_validate(
            {
                "acctId": "DU123456",
                "conid": "265598",
                "side": "BUY",
                "quantity": 1,
                "orderType": "LMT",
                "tif": "DAY",
            }
        )
