from ib_client.client import IBClient
from ib_client.settings import Settings


def test_parse_brokerage_accounts_from_strings() -> None:
    client = IBClient(Settings())

    parsed = client._parse_brokerage_accounts(["U1234567", "DU7654321"])

    assert [account.identifier for account in parsed] == ["U1234567", "DU7654321"]


def test_parse_brokerage_accounts_from_dicts() -> None:
    client = IBClient(Settings())

    parsed = client._parse_brokerage_accounts(
        [
            {"accountId": "U1234567", "accountTitle": "Main"},
            {"id": "DU7654321"},
        ]
    )

    assert [account.identifier for account in parsed] == ["U1234567", "DU7654321"]
