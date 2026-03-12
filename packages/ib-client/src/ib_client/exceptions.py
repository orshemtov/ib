from __future__ import annotations

from typing import Any


class IBError(Exception):
    """Base exception for IB client errors."""


class ConfigurationError(IBError):
    """Raised when required runtime configuration is missing or invalid."""


class GatewayError(IBError):
    """Raised when the local Client Portal Gateway cannot be reached or started."""


class AuthenticationError(IBError):
    """Raised when the IB session cannot be authenticated."""


class HTTPRequestError(IBError):
    """Raised when an HTTP request fails."""

    def __init__(self, message: str, status_code: int | None = None, payload: Any = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class WebsocketError(IBError):
    """Raised when websocket setup or streaming fails."""
