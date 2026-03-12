from ib_client.gateway import GatewayManager
from ib_client.settings import Settings


def test_format_gateway_config_port_updates_existing_value() -> None:
    original = "listenPort: 5000\nlistenSsl: true\n"

    updated = GatewayManager.format_gateway_config_port(original, 5001)

    assert updated == "listenPort: 5001\nlistenSsl: true\n"


def test_format_gateway_config_port_appends_when_missing() -> None:
    original = "listenSsl: true\n"

    updated = GatewayManager.format_gateway_config_port(original, 5001)

    assert updated.endswith("listenPort: 5001\n")


def test_gateway_download_destination_uses_repo_default() -> None:
    settings = Settings()

    assert settings.gateway_dir.name == "gateway"
