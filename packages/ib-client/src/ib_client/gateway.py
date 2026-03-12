from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import httpx
from pydantic import BaseModel

from ib_client.exceptions import ConfigurationError, GatewayError
from ib_client.logger import get_logger
from ib_client.settings import Settings


class GatewayStartResult(BaseModel):
    started: bool
    command: list[str]
    working_directory: str
    message: str


class GatewayDownloadResult(BaseModel):
    downloaded: bool
    url: str
    destination: str
    config_path: str
    message: str


STANDARD_GATEWAY_URL = "https://download2.interactivebrokers.com/portal/clientportal.gw.zip"
BETA_GATEWAY_URL = "https://download2.interactivebrokers.com/portal/clientportal.beta.gw.zip"


class GatewayManager:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.logger = get_logger("ib_client.gateway")

    def _resolve_command(self) -> tuple[list[str], str]:
        if self.settings.gateway_dir is None:
            raise ConfigurationError("IB_GATEWAY_DIR is required to start the gateway")

        script_name = "run.bat" if sys.platform.startswith("win") else "run.sh"
        script_path = self.settings.gateway_dir / "bin" / script_name
        if not script_path.exists():
            raise ConfigurationError(f"Gateway launcher not found at {script_path}")

        config_path = self.settings.gateway_config_path or (
            self.settings.gateway_dir / "root" / "conf.yaml"
        )
        if not config_path.exists():
            raise ConfigurationError(f"Gateway config not found at {config_path}")

        config_argument = str(config_path)
        working_directory = str(self.settings.gateway_dir)
        if config_path.is_relative_to(self.settings.gateway_dir):
            config_argument = str(config_path.relative_to(self.settings.gateway_dir))

        return [str(script_path), config_argument], working_directory

    def download_latest(self, beta: bool = False) -> GatewayDownloadResult:
        download_url = BETA_GATEWAY_URL if beta else STANDARD_GATEWAY_URL
        gateway_dir = self.settings.gateway_dir
        gateway_dir.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as archive_file:
            archive_path = Path(archive_file.name)

        try:
            self.logger.info("downloading_gateway", url=download_url, destination=str(gateway_dir))
            with httpx.stream(
                "GET",
                download_url,
                follow_redirects=True,
                timeout=120.0,
            ) as response:
                response.raise_for_status()
                with archive_path.open("wb") as archive_handle:
                    for chunk in response.iter_bytes():
                        archive_handle.write(chunk)

            if gateway_dir.exists():
                shutil.rmtree(gateway_dir)
            gateway_dir.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(archive_path) as gateway_archive:
                gateway_archive.extractall(gateway_dir)

            config_path = self.settings.gateway_config_path or gateway_dir / "root" / "conf.yaml"
            if not config_path.exists():
                raise GatewayError(f"Downloaded gateway config not found at {config_path}")

            self._set_listen_port(config_path, self.settings.api_port)
        finally:
            archive_path.unlink(missing_ok=True)

        return GatewayDownloadResult(
            downloaded=True,
            url=download_url,
            destination=str(gateway_dir),
            config_path=str(config_path),
            message="Gateway downloaded and configured successfully",
        )

    def start(self) -> GatewayStartResult:
        command, working_directory = self._resolve_command()
        self.logger.info("starting_gateway", command=command)
        subprocess.Popen(command, cwd=working_directory)
        return GatewayStartResult(
            started=True,
            command=command,
            working_directory=working_directory,
            message="Gateway launch command started",
        )

    def is_reachable(self) -> bool:
        try:
            response = httpx.get(
                self.settings.gateway_origin,
                verify=self.settings.verify_ssl,
                timeout=self.settings.request_timeout_seconds,
            )
        except httpx.HTTPError as exc:
            self.logger.info("gateway_unreachable", error=str(exc))
            return False
        self.logger.info("gateway_reachable", status_code=response.status_code)
        return response.status_code < 500

    def require_reachable(self) -> None:
        if not self.is_reachable():
            raise GatewayError(
                f"Client Portal Gateway is not reachable at {self.settings.gateway_origin}"
            )

    @staticmethod
    def format_gateway_config_port(config_text: str, port: int) -> str:
        updated_text, substitutions = re.subn(
            r"(?m)^(\s*listenPort:\s*)\d+(\s*)$",
            rf"\g<1>{port}\g<2>",
            config_text,
        )
        if substitutions == 0:
            suffix = "\n" if config_text.endswith("\n") else ""
            return f"{config_text}{suffix}listenPort: {port}\n"
        return updated_text

    def _set_listen_port(self, config_path: Path, port: int) -> None:
        config_text = config_path.read_text(encoding="utf-8")
        config_path.write_text(
            self.format_gateway_config_port(config_text, port),
            encoding="utf-8",
        )
