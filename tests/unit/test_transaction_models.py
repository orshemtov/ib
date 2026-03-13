import pytest

from ib_client.models.transactions import TransactionHistoryRequest, TransactionHistoryResponse


def test_transaction_history_request_requires_single_conid() -> None:
    with pytest.raises(ValueError, match="exactly one conid is required"):
        TransactionHistoryRequest.model_validate(
            {
                "acctIds": ["DU123456"],
                "conids": ["1", "2"],
                "currency": "USD",
            }
        )


def test_transaction_history_response_parses_transactions() -> None:
    response = TransactionHistoryResponse.model_validate(
        {
            "rc": 0,
            "nd": 30,
            "currency": "USD",
            "transactions": [
                {
                    "date": "2026-03-01",
                    "cur": "USD",
                    "acctid": "DU123456",
                    "amt": 500.0,
                    "conid": "265598",
                    "type": "Transfer",
                    "desc": "Deposit from bank",
                }
            ],
        }
    )

    assert response.return_code == 0
    assert response.day_count == 30
    assert len(response.transactions) == 1
    assert response.transactions[0].type == "Transfer"
    assert response.transactions[0].description == "Deposit from bank"
