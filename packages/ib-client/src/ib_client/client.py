from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from pydantic import TypeAdapter

from ib_client.exceptions import HTTPRequestError
from ib_client.http import HTTPClient
from ib_client.logger import get_logger
from ib_client.models.account import Account, AccountSummary, Position, ProfitAndLoss
from ib_client.models.market import ContractSearchResult, MarketSnapshot
from ib_client.models.order import (
    LiveOrdersResponse,
    OrderRequest,
    OrderResponseEnvelope,
    OrderResponseItem,
)
from ib_client.models.session import AuthenticationStatus, TickleResponse
from ib_client.settings import Settings
from ib_client.websocket import WebsocketClient


class IBClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.http = HTTPClient(settings)
        self.websocket = WebsocketClient(settings)
        self.logger = get_logger("ib_client.client")

    async def __aenter__(self) -> IBClient:
        await self.http.__aenter__()
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        await self.http.__aexit__(exc_type, exc, tb)

    async def get_auth_status(self) -> AuthenticationStatus:
        try:
            payload = await self.http.post_json("/iserver/auth/status")
        except HTTPRequestError as exc:
            if exc.status_code == 401:
                self.logger.info("auth_status_unauthenticated")
                return AuthenticationStatus(authenticated=False, connected=False)
            raise
        return AuthenticationStatus.model_validate(payload)

    async def initialize_brokerage_session(self) -> AuthenticationStatus:
        payload = await self.http.post_json("/iserver/auth/ssodh/init")
        return AuthenticationStatus.model_validate(payload)

    async def tickle(self) -> TickleResponse:
        payload = await self.http.post_json("/tickle")
        return TickleResponse.model_validate(payload)

    async def wait_for_authentication(self, timeout_seconds: float) -> AuthenticationStatus:
        deadline = asyncio.get_running_loop().time() + timeout_seconds
        last_status = AuthenticationStatus(authenticated=False, connected=False)
        saw_unauthenticated = False
        while asyncio.get_running_loop().time() < deadline:
            last_status = await self.get_auth_status()
            if last_status.authenticated:
                if saw_unauthenticated:
                    self.logger.info("auth_status_authenticated")
                if not last_status.connected:
                    initialized = await self.initialize_brokerage_session()
                    if initialized.connected or initialized.authenticated:
                        return initialized
                return last_status
            saw_unauthenticated = True
            await asyncio.sleep(5)
        return last_status

    async def list_accounts(self) -> list[Account]:
        payload = await self.http.get_json("/portfolio/accounts")
        return TypeAdapter(list[Account]).validate_python(payload)

    async def list_brokerage_accounts(self) -> list[Account]:
        payload = await self.http.get_json("/iserver/accounts")
        accounts_payload = payload.get("accounts") if isinstance(payload, dict) else payload
        return self._parse_brokerage_accounts(accounts_payload)

    def _parse_brokerage_accounts(self, accounts_payload: Any) -> list[Account]:
        if not isinstance(accounts_payload, list):
            raise TypeError("Expected /iserver/accounts to return a list of accounts")

        normalized_accounts: list[dict[str, Any]] = []
        for item in accounts_payload:
            if isinstance(item, str):
                normalized_accounts.append({"accountId": item})
            elif isinstance(item, dict):
                normalized_accounts.append(item)
            else:
                raise TypeError(f"Unexpected account payload item type: {type(item)!r}")

        return TypeAdapter(list[Account]).validate_python(normalized_accounts)

    async def resolve_account_id(self) -> str:
        if self.settings.account_id:
            return self.settings.account_id
        accounts = await self.list_brokerage_accounts()
        for account in accounts:
            if account.identifier:
                return account.identifier
        accounts = await self.list_accounts()
        for account in accounts:
            if account.identifier:
                return account.identifier
        raise ValueError("No account ID could be resolved from settings or API")

    async def get_account_summary(self, account_id: str) -> AccountSummary:
        payload = await self.http.get_json(f"/portfolio/{account_id}/summary")
        return AccountSummary.model_validate(payload)

    async def list_positions(self, account_id: str) -> list[Position]:
        payload = await self.http.get_json(f"/portfolio2/{account_id}/positions")
        return TypeAdapter(list[Position]).validate_python(payload)

    async def get_profit_and_loss(self) -> list[ProfitAndLoss]:
        payload = await self.http.get_json("/iserver/account/pnl/partitioned")
        return self._parse_profit_and_loss(payload)

    async def search_contract(self, symbol: str) -> list[ContractSearchResult]:
        payload = await self.http.get_json("/iserver/secdef/search", params={"symbol": symbol})
        return TypeAdapter(list[ContractSearchResult]).validate_python(payload)

    async def get_market_snapshot(
        self, conids: list[str], fields: list[str]
    ) -> list[MarketSnapshot]:
        await self.list_brokerage_accounts()
        payload = await self.http.get_json(
            "/iserver/marketdata/snapshot",
            params={"conids": ",".join(conids), "fields": ",".join(fields)},
        )
        return TypeAdapter(list[MarketSnapshot]).validate_python(payload)

    async def list_live_orders(self, force: bool = False) -> LiveOrdersResponse:
        payload = await self.http.get_json(
            "/iserver/account/orders",
            params={"force": str(force).lower()},
        )
        return LiveOrdersResponse.model_validate(payload)

    async def preview_order(self, request: OrderRequest) -> OrderResponseEnvelope:
        payload = await self.http.post_json(
            f"/iserver/account/{request.account_id}/orders/whatif",
            json=request.to_payload(),
        )
        return self._parse_order_response(payload)

    async def place_order(self, request: OrderRequest) -> OrderResponseEnvelope:
        payload = await self.http.post_json(
            f"/iserver/account/{request.account_id}/orders",
            json=request.to_payload(),
        )
        return self._parse_order_response(payload)

    async def reply_to_order_prompt(
        self, reply_id: str, confirmed: bool = True
    ) -> OrderResponseEnvelope:
        payload = await self.http.post_json(
            f"/iserver/reply/{reply_id}",
            json={"confirmed": confirmed},
        )
        return self._parse_order_response(payload)

    def _parse_order_response(self, payload: Any) -> OrderResponseEnvelope:
        if isinstance(payload, list):
            items = TypeAdapter(list[OrderResponseItem]).validate_python(payload)
            return OrderResponseEnvelope(items=items)
        if isinstance(payload, dict) and "orders" in payload:
            items = TypeAdapter(list[OrderResponseItem]).validate_python(payload["orders"])
            return OrderResponseEnvelope(items=items)
        return OrderResponseEnvelope(items=[OrderResponseItem.model_validate(payload)])

    def _parse_profit_and_loss(self, payload: Any) -> list[ProfitAndLoss]:
        if isinstance(payload, list):
            return TypeAdapter(list[ProfitAndLoss]).validate_python(payload)

        if not isinstance(payload, dict):
            raise TypeError("Expected /iserver/account/pnl/partitioned to return a dict or list")

        normalized_rows: list[dict[str, Any]] = []
        for row_group in payload.values():
            if not isinstance(row_group, dict):
                continue
            for row_key, row_value in row_group.items():
                if not isinstance(row_value, dict):
                    continue
                account_id = row_key.split(".", 1)[0]
                normalized_rows.append({"acctId": account_id, **row_value})

        return TypeAdapter(list[ProfitAndLoss]).validate_python(normalized_rows)

    async def stream_topic(self, topic: str) -> AsyncIterator[dict[str, Any]]:
        session = await self.tickle()
        async for message in self.websocket.stream(session, topic):
            yield message
