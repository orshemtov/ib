from ib_client.client import IBClient


def test_parse_profit_and_loss_multiple_groups() -> None:
    client = IBClient()

    parsed = client._parse_profit_and_loss(
        {
            "upnl": {
                "U1234567.Core": {"dpl": 1.0, "upl": 2.0},
                "DU7654321.Core": {"dpl": -1.0, "upl": -2.0},
            }
        }
    )

    assert [row.account_id for row in parsed] == ["U1234567", "DU7654321"]


def test_parse_brokerage_accounts_keeps_dict_payloads() -> None:
    client = IBClient()

    parsed = client._parse_brokerage_accounts(
        [{"accountId": "U1234567", "accountTitle": "Main Account"}]
    )

    assert parsed[0].identifier == "U1234567"
    assert parsed[0].account_title == "Main Account"
