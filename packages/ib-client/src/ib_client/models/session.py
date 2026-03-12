from __future__ import annotations

from pydantic import Field

from ib_client.models.base import IBModel


class AuthenticationStatus(IBModel):
    authenticated: bool | None = None
    connected: bool | None = None
    competing: bool | None = None
    message: str | None = None
    mac: str | None = Field(default=None, alias="MAC")
    server_info: dict[str, str] | None = Field(default=None, alias="serverInfo")


class TickleResponse(IBModel):
    session: str | None = None
    sso_expires: int | None = Field(default=None, alias="ssoExpires")


class LoginResult(IBModel):
    gateway_started: bool
    browser_opened: bool
    authenticated: bool
    message: str
