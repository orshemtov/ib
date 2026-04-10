import pytest
from ib_client.client import IBClient
from ib_client.models.fx import FXConversionRequest, ResolvedCurrencyPair


def test_fx_conversion_request_uses_fx_qty_payload() -> None:
    request = FXConversionRequest.model_validate(
        {
            "acctId": "DU123456",
            "conid": "15016062",
            "side": "sell",
            "fxQty": 100.0,
            "orderType": "mkt",
            "tif": "day",
        }
    )

    assert request.to_payload() == {
        "orders": [
            {
                "acctId": "DU123456",
                "conid": "15016062",
                "side": "SELL",
                "fxQty": 100.0,
                "orderType": "MKT",
                "tif": "DAY",
                "outsideRTH": False,
                "isCcyConv": True,
            }
        ]
    }


def test_fx_conversion_request_requires_positive_fx_quantity() -> None:
    with pytest.raises(ValueError, match="fxQty must be greater than zero"):
        FXConversionRequest.model_validate(
            {
                "acctId": "DU123456",
                "conid": "15016062",
                "side": "SELL",
                "fxQty": 0,
                "orderType": "MKT",
                "tif": "DAY",
            }
        )


def test_fx_conversion_request_requires_exactly_one_contract_selector() -> None:
    with pytest.raises(ValueError, match="exactly one of conid or conidex is required"):
        FXConversionRequest.model_validate(
            {
                "acctId": "DU123456",
                "side": "SELL",
                "fxQty": 100,
                "orderType": "MKT",
                "tif": "DAY",
            }
        )


def test_fx_conversion_request_requires_price_for_limit_orders() -> None:
    with pytest.raises(ValueError, match="price is required"):
        FXConversionRequest.model_validate(
            {
                "acctId": "DU123456",
                "conid": "15016062",
                "side": "SELL",
                "fxQty": 100,
                "orderType": "LMT",
                "tif": "DAY",
            }
        )


def test_fx_conversion_side_sells_base_symbol() -> None:
    client = IBClient()

    side = client._fx_conversion_side(
        ResolvedCurrencyPair(
            source_currency="ILS",
            target_currency="USD",
            symbol="ILS.USD",
            conid="1",
        ),
        "ILS",
        "USD",
    )

    assert side == "SELL"


def test_fx_conversion_side_buys_quote_symbol() -> None:
    client = IBClient()

    side = client._fx_conversion_side(
        ResolvedCurrencyPair(
            source_currency="ILS",
            target_currency="USD",
            symbol="USD.ILS",
            conid="1",
            is_inverse=True,
        ),
        "ILS",
        "USD",
    )

    assert side == "BUY"
