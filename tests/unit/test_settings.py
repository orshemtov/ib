from ib_client.settings import Settings


def test_settings_build_urls_without_env() -> None:
    settings = Settings(api_host="127.0.0.1", api_port=5001, use_ssl=True)

    assert settings.gateway_origin == "https://127.0.0.1:5001"
    assert settings.base_url == "https://127.0.0.1:5001/v1/api"
    assert settings.websocket_url == "wss://127.0.0.1:5001/v1/api/ws"


def test_settings_support_plain_http() -> None:
    settings = Settings(api_host="localhost", api_port=8080, use_ssl=False)

    assert settings.gateway_origin == "http://localhost:8080"
    assert settings.websocket_url == "ws://localhost:8080/v1/api/ws"
