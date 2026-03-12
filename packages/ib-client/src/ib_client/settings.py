from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[4]

LogFormat = Literal["plain", "json"]
LogColor = Literal["auto", "true", "false"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="IB_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    username: str | None = None
    password: str | None = None
    account_id: str | None = None

    gateway_dir: Path = REPO_ROOT / "gateway"
    gateway_config_path: Path | None = None
    api_host: str = "localhost"
    api_port: int = 5001
    use_ssl: bool = True
    verify_ssl: bool = False
    request_timeout_seconds: float = 30.0
    tickle_interval_seconds: float = 60.0

    playwright_headless: bool = False
    playwright_timeout_seconds: float = 180.0

    log_level: str = "INFO"
    log_format: LogFormat = "plain"
    log_color: LogColor = "auto"

    @computed_field
    @property
    def scheme(self) -> str:
        return "https" if self.use_ssl else "http"

    @computed_field
    @property
    def gateway_origin(self) -> str:
        return f"{self.scheme}://{self.api_host}:{self.api_port}"

    @computed_field
    @property
    def base_url(self) -> str:
        return f"{self.gateway_origin}/v1/api"

    @computed_field
    @property
    def websocket_url(self) -> str:
        websocket_scheme = "wss" if self.use_ssl else "ws"
        return f"{websocket_scheme}://{self.api_host}:{self.api_port}/v1/api/ws"


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    return Settings()
