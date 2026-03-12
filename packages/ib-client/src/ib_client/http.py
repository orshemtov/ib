from __future__ import annotations

from typing import Any

import httpx

from ib_client.exceptions import HTTPRequestError
from ib_client.logger import get_logger
from ib_client.settings import Settings


class HTTPClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client: httpx.AsyncClient | None = None
        self._logger = get_logger("ib_client.http")

    async def __aenter__(self) -> HTTPClient:
        self._client = httpx.AsyncClient(
            base_url=self.settings.base_url,
            timeout=self.settings.request_timeout_seconds,
            verify=self.settings.verify_ssl,
        )
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def request_json(self, method: str, path: str, **kwargs: Any) -> Any:
        if self._client is None:
            raise RuntimeError("HTTPClient must be used as an async context manager")

        response = await self._client.request(method, path, **kwargs)
        self._logger.info(
            "http_request",
            method=method,
            path=path,
            status_code=response.status_code,
        )
        try:
            payload = response.json()
        except ValueError:
            payload = response.text

        if response.is_error:
            raise HTTPRequestError(
                f"Request failed for {method} {path}",
                status_code=response.status_code,
                payload=payload,
            )
        return payload

    async def get_json(self, path: str, **kwargs: Any) -> Any:
        return await self.request_json("GET", path, **kwargs)

    async def post_json(self, path: str, **kwargs: Any) -> Any:
        return await self.request_json("POST", path, **kwargs)
