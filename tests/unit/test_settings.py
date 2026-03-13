from ib_client.settings import base_url_for, gateway_origin_for, websocket_url_for


def test_settings_build_urls_without_env() -> None:
    assert gateway_origin_for(api_host="127.0.0.1", api_port=5001, use_ssl=True) == (
        "https://127.0.0.1:5001"
    )
    assert base_url_for(api_host="127.0.0.1", api_port=5001, use_ssl=True) == (
        "https://127.0.0.1:5001/v1/api"
    )
    assert websocket_url_for(api_host="127.0.0.1", api_port=5001, use_ssl=True) == (
        "wss://127.0.0.1:5001/v1/api/ws"
    )


def test_settings_support_plain_http() -> None:
    assert gateway_origin_for(api_host="localhost", api_port=8080, use_ssl=False) == (
        "http://localhost:8080"
    )
    assert websocket_url_for(api_host="localhost", api_port=8080, use_ssl=False) == (
        "ws://localhost:8080/v1/api/ws"
    )
