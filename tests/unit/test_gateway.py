import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from ib_client.gateway import GatewayManager, GatewayRemoteMetadata


def test_format_gateway_config_port_updates_existing_value() -> None:
    original = "listenPort: 5000\nlistenSsl: true\n"

    updated = GatewayManager.format_gateway_config_port(original, 5001)

    assert updated == "listenPort: 5001\nlistenSsl: true\n"


def test_format_gateway_config_port_appends_when_missing() -> None:
    original = "listenSsl: true\n"

    updated = GatewayManager.format_gateway_config_port(original, 5001)

    assert updated.endswith("listenPort: 5001\n")


def test_gateway_download_destination_uses_repo_default() -> None:
    manager = GatewayManager()

    assert manager.settings.gateway_dir == Path("gateway")


def test_local_gateway_is_current_when_size_matches_and_remote_not_newer(tmp_path) -> None:
    archive_path = tmp_path / "clientportal.gw.zip"
    archive_path.write_bytes(b"12345")
    now = datetime.now(tz=UTC)
    os.utime(archive_path, (now.timestamp(), now.timestamp()))
    manager = GatewayManager()
    remote = GatewayRemoteMetadata(
        etag='"abc"',
        last_modified=now - timedelta(seconds=1),
        size=5,
    )

    assert manager._is_local_gateway_current(archive_path, remote) is True


def test_local_gateway_is_not_current_when_size_differs(tmp_path) -> None:
    archive_path = tmp_path / "clientportal.gw.zip"
    archive_path.write_bytes(b"12345")
    manager = GatewayManager()
    remote = GatewayRemoteMetadata(etag=None, last_modified=None, size=6)

    assert manager._is_local_gateway_current(archive_path, remote) is False


def test_local_gateway_is_not_current_when_remote_is_newer(tmp_path) -> None:
    archive_path = tmp_path / "clientportal.gw.zip"
    archive_path.write_bytes(b"12345")
    local_time = datetime.now(tz=UTC) - timedelta(days=1)
    os.utime(archive_path, (local_time.timestamp(), local_time.timestamp()))
    manager = GatewayManager()
    remote = GatewayRemoteMetadata(
        etag=None,
        last_modified=local_time + timedelta(hours=1),
        size=5,
    )

    assert manager._is_local_gateway_current(archive_path, remote) is False
