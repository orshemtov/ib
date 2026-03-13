from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

LogFormat = Literal["plain", "json"]
LogColor = Literal["auto", "true", "false"]
UNSET = object()


def gateway_origin_for(*, api_host: str, api_port: int, use_ssl: bool) -> str:
    scheme = "https" if use_ssl else "http"
    return f"{scheme}://{api_host}:{api_port}"


def base_url_for(*, api_host: str, api_port: int, use_ssl: bool) -> str:
    return f"{gateway_origin_for(api_host=api_host, api_port=api_port, use_ssl=use_ssl)}/v1/api"


def websocket_url_for(*, api_host: str, api_port: int, use_ssl: bool) -> str:
    websocket_scheme = "wss" if use_ssl else "ws"
    return f"{websocket_scheme}://{api_host}:{api_port}/v1/api/ws"


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

    gateway_dir: Path = Path("gateway")
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
        return gateway_origin_for(
            api_host=self.api_host, api_port=self.api_port, use_ssl=self.use_ssl
        )

    @computed_field
    @property
    def base_url(self) -> str:
        return base_url_for(api_host=self.api_host, api_port=self.api_port, use_ssl=self.use_ssl)

    @computed_field
    @property
    def websocket_url(self) -> str:
        return websocket_url_for(
            api_host=self.api_host, api_port=self.api_port, use_ssl=self.use_ssl
        )


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    return Settings()


def build_settings(
    *,
    username: str | None | object = UNSET,
    password: str | None | object = UNSET,
    account_id: str | None | object = UNSET,
    gateway_dir: str | Path | object = UNSET,
    gateway_config_path: str | Path | None | object = UNSET,
    api_host: str | object = UNSET,
    api_port: int | object = UNSET,
    use_ssl: bool | object = UNSET,
    verify_ssl: bool | object = UNSET,
    request_timeout_seconds: float | object = UNSET,
    tickle_interval_seconds: float | object = UNSET,
    playwright_headless: bool | object = UNSET,
    playwright_timeout_seconds: float | object = UNSET,
    log_level: str | object = UNSET,
    log_format: LogFormat | object = UNSET,
    log_color: LogColor | object = UNSET,
) -> Settings:
    values: dict[str, Any] = {}
    for key, value in {
        "username": username,
        "password": password,
        "account_id": account_id,
        "gateway_dir": gateway_dir,
        "gateway_config_path": gateway_config_path,
        "api_host": api_host,
        "api_port": api_port,
        "use_ssl": use_ssl,
        "verify_ssl": verify_ssl,
        "request_timeout_seconds": request_timeout_seconds,
        "tickle_interval_seconds": tickle_interval_seconds,
        "playwright_headless": playwright_headless,
        "playwright_timeout_seconds": playwright_timeout_seconds,
        "log_level": log_level,
        "log_format": log_format,
        "log_color": log_color,
    }.items():
        if value is UNSET:
            continue
        if key in {"gateway_dir", "gateway_config_path"} and isinstance(value, str | Path):
            values[key] = Path(value)
            continue
        values[key] = value

    return Settings(**values)


def settings_as_kwargs(settings: Settings) -> dict[str, Any]:
    return {
        "username": settings.username,
        "password": settings.password,
        "account_id": settings.account_id,
        "gateway_dir": settings.gateway_dir,
        "gateway_config_path": settings.gateway_config_path,
        "api_host": settings.api_host,
        "api_port": settings.api_port,
        "use_ssl": settings.use_ssl,
        "verify_ssl": settings.verify_ssl,
        "request_timeout_seconds": settings.request_timeout_seconds,
        "tickle_interval_seconds": settings.tickle_interval_seconds,
        "playwright_headless": settings.playwright_headless,
        "playwright_timeout_seconds": settings.playwright_timeout_seconds,
        "log_level": settings.log_level,
        "log_format": settings.log_format,
        "log_color": settings.log_color,
    }


def client_kwargs_from_settings(settings: Settings) -> dict[str, Any]:
    return {
        "account_id": settings.account_id,
        "api_host": settings.api_host,
        "api_port": settings.api_port,
        "use_ssl": settings.use_ssl,
        "verify_ssl": settings.verify_ssl,
        "request_timeout_seconds": settings.request_timeout_seconds,
        "tickle_interval_seconds": settings.tickle_interval_seconds,
    }


def gateway_kwargs_from_settings(settings: Settings) -> dict[str, Any]:
    return {
        "gateway_dir": settings.gateway_dir,
        "gateway_config_path": settings.gateway_config_path,
        "api_port": settings.api_port,
        "api_host": settings.api_host,
        "use_ssl": settings.use_ssl,
        "verify_ssl": settings.verify_ssl,
        "request_timeout_seconds": settings.request_timeout_seconds,
    }


def auth_kwargs_from_settings(settings: Settings) -> dict[str, Any]:
    return {
        "username": settings.username,
        "password": settings.password,
        **gateway_kwargs_from_settings(settings),
        "tickle_interval_seconds": settings.tickle_interval_seconds,
        "playwright_headless": settings.playwright_headless,
        "playwright_timeout_seconds": settings.playwright_timeout_seconds,
    }


def logging_kwargs_from_settings(settings: Settings) -> dict[str, Any]:
    return {
        "log_level": settings.log_level,
        "log_format": settings.log_format,
        "log_color": settings.log_color,
    }
