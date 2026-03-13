from ib_client.models.session import AuthenticationStatus


def test_authentication_status_allows_null_server_info_values() -> None:
    status = AuthenticationStatus.model_validate(
        {
            "authenticated": True,
            "connected": True,
            "serverInfo": {
                "serverName": None,
                "serverVersion": None,
            },
        }
    )

    assert status.authenticated is True
    assert status.connected is True
    assert status.server_info == {
        "serverName": None,
        "serverVersion": None,
    }
