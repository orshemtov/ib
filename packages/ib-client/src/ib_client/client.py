from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from pydantic import TypeAdapter

from ib_client.exceptions import HTTPRequestError
from ib_client.http import HTTPClient
from ib_client.logger import get_logger
from ib_client.models.account import Account, AccountSummary, Position, ProfitAndLoss
from ib_client.models.history import HistoricalDataResponse
from ib_client.models.fx import (
    CurrencyPair,
    ExchangeRate,
    FXCloseToUSDPlacement,
    FXCloseToUSDPlan,
    FXCloseToUSDPreview,
    FXConversionRequest,
    ResolvedCurrencyPair,
)
from ib_client.models.market import ContractSearchResult, MarketSnapshot
from ib_client.models.options import (
    ContractRule,
    OptionContract,
    OptionStrikes,
    SecurityDefinition,
    StockLookupContract,
)
from ib_client.models.order import (
    LiveOrdersResponse,
    OrderRequest,
    OrderResponseEnvelope,
    OrderResponseItem,
)
from ib_client.models.portfolio import ComboPosition, LedgerEntry
from ib_client.models.session import AuthenticationStatus, TickleResponse
from ib_client.models.transactions import (
    TransactionHistoryRequest,
    TransactionHistoryResponse,
    TransactionRecord,
)
from ib_client.models.trading import OrderStatus, ScannerParameters, ScannerResult, Trade, Watchlist
from ib_client.settings import Settings, build_settings
from ib_client.websocket import WebsocketClient


class IBClient:
    def __init__(
        self,
        settings: Settings | None = None,
        *,
        account_id: str | None = None,
        api_host: str = "localhost",
        api_port: int = 5001,
        use_ssl: bool = True,
        verify_ssl: bool = False,
        request_timeout_seconds: float = 30.0,
        tickle_interval_seconds: float = 60.0,
    ) -> None:
        self.settings = settings or build_settings(
            account_id=account_id,
            api_host=api_host,
            api_port=api_port,
            use_ssl=use_ssl,
            verify_ssl=verify_ssl,
            request_timeout_seconds=request_timeout_seconds,
            tickle_interval_seconds=tickle_interval_seconds,
        )
        self.http = HTTPClient(
            api_host=self.settings.api_host,
            api_port=self.settings.api_port,
            use_ssl=self.settings.use_ssl,
            verify_ssl=self.settings.verify_ssl,
            request_timeout_seconds=self.settings.request_timeout_seconds,
        )
        self.websocket = WebsocketClient(
            api_host=self.settings.api_host,
            api_port=self.settings.api_port,
            use_ssl=self.settings.use_ssl,
        )
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

    async def get_account_ledger(self, account_id: str) -> dict[str, LedgerEntry]:
        payload = await self.http.get_json(f"/portfolio/{account_id}/ledger")
        if not isinstance(payload, dict):
            raise TypeError("Expected /portfolio/{accountId}/ledger to return a dict")
        return {currency: LedgerEntry.model_validate(entry) for currency, entry in payload.items()}

    async def list_combo_positions(self, account_id: str) -> list[ComboPosition]:
        payload = await self.http.get_json(f"/portfolio/{account_id}/combo/positions")
        return TypeAdapter(list[ComboPosition]).validate_python(payload)

    async def invalidate_positions(self, account_id: str) -> dict[str, Any]:
        payload = await self.http.post_json(f"/portfolio/{account_id}/positions/invalidate")
        if not isinstance(payload, dict):
            raise TypeError("Expected positions invalidate response to be a dict")
        return payload

    async def search_contract(self, symbol: str) -> list[ContractSearchResult]:
        payload = await self.http.get_json("/iserver/secdef/search", params={"symbol": symbol})
        return TypeAdapter(list[ContractSearchResult]).validate_python(payload)

    async def list_currency_pairs(self, currency: str) -> list[CurrencyPair]:
        requested_currency = currency.upper()
        payload = await self.http.get_json(
            "/iserver/currency/pairs",
            params={"currency": requested_currency},
        )
        if not isinstance(payload, dict):
            raise TypeError("Expected /iserver/currency/pairs to return a dict")
        pair_payload = payload.get(requested_currency, [])
        if not isinstance(pair_payload, list):
            raise TypeError("Expected requested currency pair payload to be a list")
        return [
            CurrencyPair.model_validate({"requested_currency": requested_currency, **entry})
            for entry in pair_payload
        ]

    async def get_exchange_rate(self, source_currency: str, target_currency: str) -> ExchangeRate:
        source = source_currency.upper()
        target = target_currency.upper()
        payload = await self.http.get_json(
            "/iserver/exchangerate",
            params={"source": source, "target": target},
        )
        if not isinstance(payload, dict):
            raise TypeError("Expected /iserver/exchangerate to return a dict")
        return ExchangeRate.model_validate(
            {
                "source_currency": source,
                "target_currency": target,
                **payload,
            }
        )

    async def resolve_currency_pair(
        self,
        source_currency: str,
        target_currency: str,
    ) -> ResolvedCurrencyPair:
        source = source_currency.upper()
        target = target_currency.upper()
        requested_currencies = [target]
        if source != target:
            requested_currencies.append(source)

        direct_symbol = f"{target}.{source}"
        inverse_symbol = f"{source}.{target}"

        for requested_currency in requested_currencies:
            pairs = await self.list_currency_pairs(requested_currency)
            for pair in pairs:
                if pair.symbol == direct_symbol and pair.conid is not None:
                    return ResolvedCurrencyPair(
                        source_currency=source,
                        target_currency=target,
                        symbol=direct_symbol,
                        conid=pair.conid,
                        is_inverse=False,
                    )
            for pair in pairs:
                if pair.symbol == inverse_symbol and pair.conid is not None:
                    return ResolvedCurrencyPair(
                        source_currency=source,
                        target_currency=target,
                        symbol=inverse_symbol,
                        conid=pair.conid,
                        is_inverse=True,
                    )

        raise ValueError(f"No currency pair found for {source}/{target}")

    def _fx_conversion_side(
        self,
        pair: ResolvedCurrencyPair,
        source_currency: str,
        target_currency: str,
    ) -> str:
        source = source_currency.upper()
        target = target_currency.upper()
        if pair.symbol == f"{source}.{target}":
            return "SELL"
        if pair.symbol == f"{target}.{source}":
            return "BUY"
        raise ValueError(f"Resolved pair {pair.symbol} does not match {source}/{target}")

    async def build_fx_conversion_request(
        self,
        source_currency: str,
        target_currency: str,
        amount: float,
        *,
        account_id: str | None = None,
        order_type: str = "MKT",
        tif: str = "DAY",
        price: float | None = None,
    ) -> tuple[ResolvedCurrencyPair, FXConversionRequest]:
        resolved_account_id = account_id or await self.resolve_account_id()
        pair = await self.resolve_currency_pair(source_currency, target_currency)
        side = self._fx_conversion_side(pair, source_currency, target_currency)
        request = FXConversionRequest.model_validate(
            {
                "acctId": resolved_account_id,
                "conid": pair.conid,
                "side": side,
                "fxQty": amount,
                "orderType": order_type,
                "tif": tif,
                "price": price,
                "isCcyConv": True,
            }
        )
        return pair, request

    async def lookup_stocks(self, symbols: list[str]) -> dict[str, list[StockLookupContract]]:
        payload = await self.http.get_json("/trsrv/stocks", params={"symbols": ",".join(symbols)})
        if not isinstance(payload, dict):
            raise TypeError("Expected /trsrv/stocks to return a dict")
        return {
            symbol: TypeAdapter(list[StockLookupContract]).validate_python(items)
            for symbol, items in payload.items()
        }

    async def get_security_definition(self, conids: list[str]) -> list[SecurityDefinition]:
        payload = await self.http.get_json("/trsrv/secdef", params={"conids": ",".join(conids)})
        secdef_payload = payload.get("secdef") if isinstance(payload, dict) else payload
        return TypeAdapter(list[SecurityDefinition]).validate_python(secdef_payload)

    async def get_option_strikes(
        self,
        conid: str,
        sec_type: str,
        month: str,
        exchange: str | None = None,
    ) -> OptionStrikes:
        params = {"conid": conid, "sectype": sec_type, "month": month}
        if exchange:
            params["exchange"] = exchange
        payload = await self.http.get_json("/iserver/secdef/strikes", params=params)
        return OptionStrikes.model_validate(payload)

    async def get_option_contracts(
        self,
        conid: str,
        sec_type: str,
        month: str,
        strike: str,
        right: str,
        exchange: str | None = None,
    ) -> list[OptionContract]:
        params = {
            "conid": conid,
            "sectype": sec_type,
            "month": month,
            "strike": strike,
            "right": right,
        }
        if exchange:
            params["exchange"] = exchange
        payload = await self.http.get_json("/iserver/secdef/info", params=params)
        return TypeAdapter(list[OptionContract]).validate_python(payload)

    async def get_contract_rules(
        self,
        conid: str,
        is_buy: bool = True,
        exchange: str | None = None,
        modify_order: bool = False,
        order_id: str | None = None,
    ) -> ContractRule:
        request_body: dict[str, Any] = {
            "conid": conid,
            "isBuy": is_buy,
            "modifyOrder": modify_order,
        }
        if exchange:
            request_body["exchange"] = exchange
        if order_id:
            request_body["orderId"] = order_id
        payload = await self.http.post_json("/iserver/contract/rules", json=request_body)
        return ContractRule.model_validate(payload)

    async def get_market_snapshot(
        self, conids: list[str], fields: list[str]
    ) -> list[MarketSnapshot]:
        await self.list_brokerage_accounts()
        payload = await self.http.get_json(
            "/iserver/marketdata/snapshot",
            params={"conids": ",".join(conids), "fields": ",".join(fields)},
        )
        return TypeAdapter(list[MarketSnapshot]).validate_python(payload)

    async def get_historical_data(
        self,
        conid: str,
        period: str = "1d",
        bar: str = "1h",
        exchange: str | None = None,
        outside_rth: bool = False,
    ) -> HistoricalDataResponse:
        params = {
            "conid": conid,
            "period": period,
            "bar": bar,
            "outsideRth": str(outside_rth).lower(),
        }
        if exchange:
            params["exchange"] = exchange
        payload = await self.http.get_json("/iserver/marketdata/history", params=params)
        return HistoricalDataResponse.model_validate(payload)

    async def list_live_orders(self, force: bool = False) -> LiveOrdersResponse:
        payload = await self.http.get_json(
            "/iserver/account/orders",
            params={"force": str(force).lower()},
        )
        return LiveOrdersResponse.model_validate(payload)

    async def get_order_status(self, order_id: str) -> OrderStatus:
        payload = await self.http.get_json(f"/iserver/account/order/status/{order_id}")
        return OrderStatus.model_validate(payload)

    async def modify_order(self, request: OrderRequest, order_id: str) -> OrderResponseEnvelope:
        payload = await self.http.post_json(
            f"/iserver/account/{request.account_id}/order/{order_id}",
            json=request.to_payload(),
        )
        return self._parse_order_response(payload)

    async def cancel_order(self, account_id: str, order_id: str) -> dict[str, Any]:
        payload = await self.http.request_json(
            "DELETE",
            f"/iserver/account/{account_id}/order/{order_id}",
        )
        if not isinstance(payload, dict):
            raise TypeError("Expected cancel order response to be a dict")
        return payload

    async def switch_account(self, account_id: str) -> dict[str, Any]:
        payload = await self.http.post_json("/iserver/account", json={"acctId": account_id})
        if not isinstance(payload, dict):
            raise TypeError("Expected switch account response to be a dict")
        return payload

    async def preview_order(self, request: OrderRequest) -> OrderResponseEnvelope:
        payload = await self.http.post_json(
            f"/iserver/account/{request.account_id}/orders/whatif",
            json=request.to_payload(),
        )
        return self._parse_order_response(payload)

    async def preview_fx_conversion(self, request: FXConversionRequest) -> OrderResponseEnvelope:
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

    async def place_fx_conversion(self, request: FXConversionRequest) -> OrderResponseEnvelope:
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

    async def list_trades(self) -> list[Trade]:
        payload = await self.http.get_json("/iserver/account/trades")
        return TypeAdapter(list[Trade]).validate_python(payload)

    async def get_transaction_history(
        self,
        request: TransactionHistoryRequest,
    ) -> TransactionHistoryResponse:
        payload = await self.http.post_json("/pa/transactions", json=request.to_payload())
        return TransactionHistoryResponse.model_validate(payload)

    async def get_account_transaction_history(
        self,
        conid: str | int,
        *,
        account_id: str | None = None,
        currency: str = "USD",
        days: int | None = None,
    ) -> TransactionHistoryResponse:
        resolved_account_id = account_id or await self.resolve_account_id()
        request = TransactionHistoryRequest.model_validate(
            {
                "acctIds": [resolved_account_id],
                "conids": [conid],
                "currency": currency.upper(),
                "days": days,
            }
        )
        return await self.get_transaction_history(request)

    async def list_funding_transactions(
        self,
        conid: str | int,
        *,
        account_id: str | None = None,
        currency: str = "USD",
        days: int | None = None,
    ) -> list[TransactionRecord]:
        history = await self.get_account_transaction_history(
            conid,
            account_id=account_id,
            currency=currency,
            days=days,
        )
        matches: list[TransactionRecord] = []
        for row in history.transactions:
            haystack = " ".join(filter(None, [row.type, row.description])).lower()
            if any(term in haystack for term in ("transfer", "deposit", "withdraw")):
                matches.append(row)
        return matches

    async def plan_close_to_usd(
        self,
        currency: str,
        *,
        account_id: str | None = None,
        amount: float | None = None,
        min_cash_balance: float = 1.0,
        order_type: str = "MKT",
        tif: str = "DAY",
        price: float | None = None,
    ) -> FXCloseToUSDPlan:
        target_currency = currency.upper()
        if target_currency == "USD":
            raise ValueError("USD is already the target currency")

        resolved_account_id = account_id or await self.resolve_account_id()
        ledger = await self.get_account_ledger(resolved_account_id)
        entry = ledger.get(target_currency)
        if entry is None or entry.cash_balance is None:
            raise ValueError(f"No cash balance found for {target_currency}")

        cash_balance = float(entry.cash_balance)
        if cash_balance <= 0:
            raise ValueError(
                f"Cash balance for {target_currency} must be positive to close into USD"
            )
        close_amount = abs(cash_balance) if amount is None else amount
        if close_amount <= 0:
            raise ValueError("amount must be greater than zero")
        if abs(cash_balance) < min_cash_balance:
            raise ValueError(
                f"Cash balance for {target_currency} is below min_cash_balance={min_cash_balance}"
            )

        pair, request = await self.build_fx_conversion_request(
            target_currency,
            "USD",
            close_amount,
            account_id=resolved_account_id,
            order_type=order_type,
            tif=tif,
            price=price,
        )
        rate = await self.get_exchange_rate(target_currency, "USD")
        return FXCloseToUSDPlan(
            account_id=resolved_account_id,
            currency=target_currency,
            cash_balance=cash_balance,
            source_currency=target_currency,
            target_currency="USD",
            pair_symbol=pair.symbol,
            pair_conid=pair.conid,
            side=request.side,
            fx_quantity=close_amount,
            estimated_rate=rate.rate,
            request=request,
        )

    async def preview_close_to_usd(
        self,
        currency: str,
        *,
        account_id: str | None = None,
        amount: float | None = None,
        min_cash_balance: float = 1.0,
        order_type: str = "MKT",
        tif: str = "DAY",
        price: float | None = None,
    ) -> FXCloseToUSDPreview:
        plan = await self.plan_close_to_usd(
            currency,
            account_id=account_id,
            amount=amount,
            min_cash_balance=min_cash_balance,
            order_type=order_type,
            tif=tif,
            price=price,
        )
        preview = await self.preview_fx_conversion(plan.request)
        return FXCloseToUSDPreview(plan=plan, preview=preview.model_dump(mode="json"))

    async def place_close_to_usd(
        self,
        currency: str,
        *,
        account_id: str | None = None,
        amount: float | None = None,
        min_cash_balance: float = 1.0,
        order_type: str = "MKT",
        tif: str = "DAY",
        price: float | None = None,
    ) -> FXCloseToUSDPlacement:
        plan = await self.plan_close_to_usd(
            currency,
            account_id=account_id,
            amount=amount,
            min_cash_balance=min_cash_balance,
            order_type=order_type,
            tif=tif,
            price=price,
        )
        placed = await self.place_fx_conversion(plan.request)
        return FXCloseToUSDPlacement(plan=plan, placed=placed.model_dump(mode="json"))

    async def get_scanner_parameters(self) -> ScannerParameters:
        payload = await self.http.get_json("/iserver/scanner/params")
        return ScannerParameters.model_validate(payload)

    async def run_scanner(
        self,
        instrument: str,
        scan_type: str,
        location: str,
        filter_values: list[dict[str, Any]] | None = None,
    ) -> list[ScannerResult]:
        payload = await self.http.post_json(
            "/iserver/scanner/run",
            json={
                "instrument": instrument,
                "type": scan_type,
                "location": location,
                "filter": filter_values or [],
            },
        )
        scanner_payload = payload.get("contracts") if isinstance(payload, dict) else payload
        return TypeAdapter(list[ScannerResult]).validate_python(scanner_payload)

    async def list_watchlists(self) -> list[Watchlist]:
        payload = await self.http.get_json("/iserver/watchlists")
        return TypeAdapter(list[Watchlist]).validate_python(payload)

    async def get_watchlist(self, watchlist_id: str) -> Watchlist:
        payload = await self.http.get_json("/iserver/watchlist", params={"id": watchlist_id})
        return Watchlist.model_validate(payload)

    async def create_watchlist(
        self,
        name: str,
        rows: list[dict[str, Any]] | None = None,
    ) -> Watchlist:
        payload = await self.http.post_json(
            "/iserver/watchlist",
            json={"id": "", "name": name, "rows": rows or []},
        )
        return Watchlist.model_validate(payload)

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

    async def stream_market_data(
        self, conid: str, fields: list[str] | None = None
    ) -> AsyncIterator[dict[str, Any]]:
        request_fields = fields or ["31", "84", "86"]
        topic = f'smd+{conid}+{{"fields":{request_fields!r}}}'.replace("'", '"')
        async for message in self.stream_topic(topic):
            yield message

    async def stream_live_orders(self) -> AsyncIterator[dict[str, Any]]:
        async for message in self.stream_topic("sor+{}"):
            yield message

    async def stream_pnl(self) -> AsyncIterator[dict[str, Any]]:
        async for message in self.stream_topic("spl+{}"):
            yield message

    async def stream_trades(self) -> AsyncIterator[dict[str, Any]]:
        async for message in self.stream_topic("str+{}"):
            yield message
