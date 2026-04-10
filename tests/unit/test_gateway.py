import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from ib_client.exceptions import ConfigurationError
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


def test_resolve_command_script_path_is_absolute(tmp_path: Path) -> None:
    script_name = "run.bat" if sys.platform.startswith("win") else "run.sh"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    script = bin_dir / script_name
    script.write_text("#!/bin/bash\n")
    script.chmod(0o755)
    config = tmp_path / "root" / "conf.yaml"
    config.parent.mkdir()
    config.write_text("listenPort: 5001\n")

    manager = GatewayManager(gateway_dir=tmp_path)
    command, working_directory = manager._resolve_command()

    assert Path(command[0]).is_absolute(), (
        "Script path must be absolute so Popen cwd does not affect it"
    )


def test_resolve_command_raises_when_script_missing(tmp_path: Path) -> None:
    manager = GatewayManager(gateway_dir=tmp_path)

    with pytest.raises(ConfigurationError, match="Gateway launcher not found"):
        manager._resolve_command()
