from __future__ import annotations

from typing import Any

import httpx

from ib_client.exceptions import HTTPRequestError
from ib_client.logger import get_logger
from ib_client.settings import base_url_for


class HTTPClient:
    def __init__(
        self,
        *,
        api_host: str = "localhost",
        api_port: int = 5001,
        use_ssl: bool = True,
        verify_ssl: bool = False,
        request_timeout_seconds: float = 30.0,
    ) -> None:
        self.api_host = api_host
        self.api_port = api_port
        self.use_ssl = use_ssl
        self.verify_ssl = verify_ssl
        self.request_timeout_seconds = request_timeout_seconds
        self._client: httpx.AsyncClient | None = None
        self._logger = get_logger("ib_client.http")

    async def __aenter__(self) -> HTTPClient:
        self._client = httpx.AsyncClient(
            base_url=base_url_for(
                api_host=self.api_host,
                api_port=self.api_port,
                use_ssl=self.use_ssl,
            ),
            timeout=self.request_timeout_seconds,
            verify=self.verify_ssl,
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
