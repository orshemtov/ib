from ib_client.client import IBClient


def test_parse_profit_and_loss_partitioned_payload() -> None:
    client = IBClient()

    parsed = client._parse_profit_and_loss(
        {
            "upnl": {
                "U1234567.Core": {
                    "dpl": -10.5,
                    "upl": 4.25,
                    "rpl": 1.5,
                }
            }
        }
    )

    assert len(parsed) == 1
    assert parsed[0].account_id == "U1234567"
    assert parsed[0].daily == -10.5
    assert parsed[0].unrealized == 4.25
    assert parsed[0].realized == 1.5
