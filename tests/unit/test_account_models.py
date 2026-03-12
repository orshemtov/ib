from ib_client.models.account import AccountSummary


def test_account_summary_extracts_amount_from_nested_values() -> None:
    summary = AccountSummary.model_validate(
        {
            "accountId": "U1234567",
            "netliquidation": {"amount": 1234.56, "currency": "USD"},
            "totalcashvalue": {"amount": 78.9, "currency": "USD"},
        }
    )

    assert summary.net_liquidation == 1234.56
    assert summary.total_cash_value == 78.9
