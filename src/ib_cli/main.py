from __future__ import annotations

import asyncio
import json
from typing import Any

import typer
from ib_client.auth import AuthWorkflow
from ib_client.client import IBClient
from ib_client.gateway import GatewayManager
from ib_client.logger import configure_logging, get_logger
from ib_client.models.order import OrderRequest
from ib_client.settings import (
    Settings,
    auth_kwargs_from_settings,
    client_kwargs_from_settings,
    gateway_kwargs_from_settings,
    load_settings,
    logging_kwargs_from_settings,
)

app = typer.Typer(help="Interactive Brokers Client Portal CLI")
auth_app = typer.Typer(help="Authentication and gateway commands")
gateway_app = typer.Typer(help="Gateway lifecycle and download commands")
accounts_app = typer.Typer(help="Account commands")
positions_app = typer.Typer(help="Position commands")
market_app = typer.Typer(help="Market data commands")
options_app = typer.Typer(help="Options and contract discovery commands")
portfolio_app = typer.Typer(help="Portfolio detail commands")
orders_app = typer.Typer(help="Order commands")
trades_app = typer.Typer(help="Trade and execution commands")
scanner_app = typer.Typer(help="Scanner commands")
fx_app = typer.Typer(help="Foreign exchange and currency conversion commands")
transactions_app = typer.Typer(help="Transaction history commands")
watchlists_app = typer.Typer(help="Watchlist commands")
ws_app = typer.Typer(help="Websocket commands")

app.add_typer(auth_app, name="auth")
app.add_typer(gateway_app, name="gateway")
app.add_typer(accounts_app, name="accounts")
app.add_typer(positions_app, name="positions")
app.add_typer(market_app, name="market")
app.add_typer(options_app, name="options")
app.add_typer(portfolio_app, name="portfolio")
app.add_typer(orders_app, name="orders")
app.add_typer(trades_app, name="trades")
app.add_typer(scanner_app, name="scanner")
app.add_typer(fx_app, name="fx")
app.add_typer(transactions_app, name="transactions")
app.add_typer(watchlists_app, name="watchlists")
app.add_typer(ws_app, name="ws")


def _settings() -> Settings:
    settings = load_settings()
    configure_logging(**logging_kwargs_from_settings(settings))
    return settings


def _print_json(data: Any) -> None:
    typer.echo(json.dumps(data, indent=2, default=str))


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


def _client(settings: Settings) -> IBClient:
    return IBClient(**client_kwargs_from_settings(settings))


def _gateway(settings: Settings) -> GatewayManager:
    return GatewayManager(**gateway_kwargs_from_settings(settings))


def _auth_workflow(settings: Settings) -> AuthWorkflow:
    return AuthWorkflow(**auth_kwargs_from_settings(settings))


@app.callback()
def cli() -> None:
    """Run the Interactive Brokers CLI."""


@auth_app.command("status")
def auth_status() -> None:
    settings = _settings()
    logger = get_logger("ib_cli.auth.status")

    async def _command() -> None:
        async with _client(settings) as client:
            status = await client.get_auth_status()
            logger.info(
                "authentication_status",
                authenticated=status.authenticated,
                connected=status.connected,
                competing=status.competing,
            )
            _print_json(status.model_dump(mode="json"))

    _run(_command())


@auth_app.command("login")
def auth_login() -> None:
    settings = _settings()
    workflow = _auth_workflow(settings)
    result = _run(workflow.login())
    _print_json(result.model_dump(mode="json"))


@auth_app.command("start-gateway")
def start_gateway() -> None:
    settings = _settings()
    manager = _gateway(settings)
    result = manager.start()
    _print_json(result.model_dump(mode="json"))


@gateway_app.command("download")
def gateway_download(
    beta: bool = typer.Option(False, help="Download the beta gateway build."),
) -> None:
    settings = _settings()
    manager = _gateway(settings)
    result = manager.download_latest(beta=beta)
    _print_json(result.model_dump(mode="json"))


@gateway_app.command("start")
def gateway_start() -> None:
    start_gateway()


@accounts_app.command("list")
def accounts_list() -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            accounts = await client.list_accounts()
            _print_json([account.model_dump(mode="json") for account in accounts])

    _run(_command())


@accounts_app.command("summary")
def accounts_summary(account_id: str | None = typer.Argument(default=None)) -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            resolved_account_id = account_id or await client.resolve_account_id()
            summary = await client.get_account_summary(resolved_account_id)
            _print_json(summary.model_dump(mode="json"))

    _run(_command())


@accounts_app.command("pnl")
def accounts_pnl() -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            pnl_rows = await client.get_profit_and_loss()
            _print_json([row.model_dump(mode="json") for row in pnl_rows])

    _run(_command())


@portfolio_app.command("ledger")
def portfolio_ledger(account_id: str | None = typer.Argument(default=None)) -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            resolved_account_id = account_id or await client.resolve_account_id()
            ledger = await client.get_account_ledger(resolved_account_id)
            _print_json(
                {currency: entry.model_dump(mode="json") for currency, entry in ledger.items()}
            )

    _run(_command())


@portfolio_app.command("combos")
def portfolio_combos(account_id: str | None = typer.Argument(default=None)) -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            resolved_account_id = account_id or await client.resolve_account_id()
            combos = await client.list_combo_positions(resolved_account_id)
            _print_json([combo.model_dump(mode="json") for combo in combos])

    _run(_command())


@portfolio_app.command("invalidate-positions")
def portfolio_invalidate_positions(account_id: str | None = typer.Argument(default=None)) -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            resolved_account_id = account_id or await client.resolve_account_id()
            result = await client.invalidate_positions(resolved_account_id)
            _print_json(result)

    _run(_command())


@positions_app.command("list")
def positions_list(account_id: str | None = typer.Argument(default=None)) -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            resolved_account_id = account_id or await client.resolve_account_id()
            positions = await client.list_positions(resolved_account_id)
            _print_json([position.model_dump(mode="json") for position in positions])

    _run(_command())


@orders_app.command("reply")
def orders_reply(reply_id: str, confirm: bool = typer.Option(True)) -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            reply = await client.reply_to_order_prompt(reply_id, confirmed=confirm)
            _print_json(reply.model_dump(mode="json"))

    _run(_command())


@market_app.command("search")
def market_search(symbol: str) -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            results = await client.search_contract(symbol)
            _print_json([result.model_dump(mode="json") for result in results])

    _run(_command())


@market_app.command("quote")
def market_quote(conids: list[str], fields: str = "31,55,84,86") -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            snapshots = await client.get_market_snapshot(conids=conids, fields=fields.split(","))
            _print_json([snapshot.model_dump(mode="json") for snapshot in snapshots])

    _run(_command())


@market_app.command("history")
def market_history(
    conid: str,
    period: str = typer.Option("1d"),
    bar: str = typer.Option("1h"),
    exchange: str | None = typer.Option(default=None),
    outside_rth: bool = typer.Option(False, "--outside-rth"),
) -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            history = await client.get_historical_data(
                conid=conid,
                period=period,
                bar=bar,
                exchange=exchange,
                outside_rth=outside_rth,
            )
            _print_json(history.model_dump(mode="json"))

    _run(_command())


@fx_app.command("pairs")
def fx_pairs(currency: str) -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            pairs = await client.list_currency_pairs(currency)
            _print_json([pair.model_dump(mode="json") for pair in pairs])

    _run(_command())


@fx_app.command("rate")
def fx_rate(
    source: str = typer.Option(...),
    target: str = typer.Option(...),
) -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            rate = await client.get_exchange_rate(source, target)
            _print_json(rate.model_dump(mode="json"))

    _run(_command())


@fx_app.command("preview")
def fx_preview(
    source: str = typer.Option(...),
    target: str = typer.Option(...),
    amount: float = typer.Option(...),
    account_id: str | None = typer.Option(default=None),
    order_type: str = typer.Option("MKT", "--order-type"),
    tif: str = typer.Option("DAY"),
    price: float | None = typer.Option(default=None),
) -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            pair, request = await client.build_fx_conversion_request(
                source,
                target,
                amount,
                account_id=account_id,
                order_type=order_type,
                tif=tif,
                price=price,
            )
            preview = await client.preview_fx_conversion(request)
            _print_json(
                {
                    "pair": pair.model_dump(mode="json"),
                    "request": request.model_dump(mode="json", by_alias=True),
                    "preview": preview.model_dump(mode="json"),
                }
            )

    _run(_command())


@fx_app.command("place")
def fx_place(
    source: str = typer.Option(...),
    target: str = typer.Option(...),
    amount: float = typer.Option(...),
    account_id: str | None = typer.Option(default=None),
    order_type: str = typer.Option("MKT", "--order-type"),
    tif: str = typer.Option("DAY"),
    price: float | None = typer.Option(default=None),
    confirm: bool = typer.Option(False, help="Required to send the FX conversion request."),
) -> None:
    settings = _settings()
    if not confirm:
        raise typer.BadParameter("Pass --confirm to send the FX conversion request.")

    async def _command() -> None:
        async with _client(settings) as client:
            pair, request = await client.build_fx_conversion_request(
                source,
                target,
                amount,
                account_id=account_id,
                order_type=order_type,
                tif=tif,
                price=price,
            )
            placed = await client.place_fx_conversion(request)
            _print_json(
                {
                    "pair": pair.model_dump(mode="json"),
                    "request": request.model_dump(mode="json", by_alias=True),
                    "placed": placed.model_dump(mode="json"),
                }
            )

    _run(_command())


@fx_app.command("preview-close-to-usd")
def fx_preview_close_to_usd(
    currency: str,
    account_id: str | None = typer.Option(default=None),
    amount: float | None = typer.Option(default=None),
    min_cash_balance: float = typer.Option(1.0, "--min-cash-balance"),
    order_type: str = typer.Option("MKT", "--order-type"),
    tif: str = typer.Option("DAY"),
    price: float | None = typer.Option(default=None),
) -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            preview = await client.preview_close_to_usd(
                currency,
                account_id=account_id,
                amount=amount,
                min_cash_balance=min_cash_balance,
                order_type=order_type,
                tif=tif,
                price=price,
            )
            _print_json(preview.model_dump(mode="json"))

    _run(_command())


@fx_app.command("place-close-to-usd")
def fx_place_close_to_usd(
    currency: str,
    account_id: str | None = typer.Option(default=None),
    amount: float | None = typer.Option(default=None),
    min_cash_balance: float = typer.Option(1.0, "--min-cash-balance"),
    order_type: str = typer.Option("MKT", "--order-type"),
    tif: str = typer.Option("DAY"),
    price: float | None = typer.Option(default=None),
    confirm: bool = typer.Option(False, help="Required to send the FX close request."),
) -> None:
    settings = _settings()
    if not confirm:
        raise typer.BadParameter("Pass --confirm to send the FX close request.")

    async def _command() -> None:
        async with _client(settings) as client:
            placed = await client.place_close_to_usd(
                currency,
                account_id=account_id,
                amount=amount,
                min_cash_balance=min_cash_balance,
                order_type=order_type,
                tif=tif,
                price=price,
            )
            _print_json(placed.model_dump(mode="json"))

    _run(_command())


@options_app.command("stocks")
def options_stocks(symbols: list[str]) -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            results = await client.lookup_stocks(symbols)
            _print_json(
                {
                    symbol: [item.model_dump(mode="json") for item in items]
                    for symbol, items in results.items()
                }
            )

    _run(_command())


@options_app.command("secdef")
def options_secdef(conids: list[str]) -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            results = await client.get_security_definition(conids)
            _print_json([item.model_dump(mode="json") for item in results])

    _run(_command())


@options_app.command("strikes")
def options_strikes(
    conid: str,
    sec_type: str = typer.Option("OPT", "--sec-type"),
    month: str = typer.Option(...),
    exchange: str | None = typer.Option(default=None),
) -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            strikes = await client.get_option_strikes(
                conid=conid,
                sec_type=sec_type,
                month=month,
                exchange=exchange,
            )
            _print_json(strikes.model_dump(mode="json"))

    _run(_command())


@options_app.command("contracts")
def options_contracts(
    conid: str,
    month: str,
    strike: str,
    right: str,
    sec_type: str = typer.Option("OPT", "--sec-type"),
    exchange: str | None = typer.Option(default=None),
) -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            contracts = await client.get_option_contracts(
                conid=conid,
                sec_type=sec_type,
                month=month,
                strike=strike,
                right=right.upper(),
                exchange=exchange,
            )
            _print_json([item.model_dump(mode="json") for item in contracts])

    _run(_command())


@options_app.command("rules")
def options_rules(
    conid: str,
    exchange: str | None = typer.Option(default=None),
    is_buy: bool = typer.Option(True, "--is-buy/--is-sell"),
    modify_order: bool = typer.Option(False),
    order_id: str | None = typer.Option(default=None),
) -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            rules = await client.get_contract_rules(
                conid=conid,
                exchange=exchange,
                is_buy=is_buy,
                modify_order=modify_order,
                order_id=order_id,
            )
            _print_json(rules.model_dump(mode="json"))

    _run(_command())


@orders_app.command("list")
def orders_list(force: bool = False) -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            orders = await client.list_live_orders(force=force)
            _print_json(orders.model_dump(mode="json"))

    _run(_command())


@orders_app.command("status")
def orders_status(order_id: str) -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            status = await client.get_order_status(order_id)
            _print_json(status.model_dump(mode="json"))

    _run(_command())


@orders_app.command("preview")
def orders_preview(
    conid: str,
    side: str,
    quantity: float,
    order_type: str = typer.Option("MKT", "--order-type"),
    tif: str = typer.Option("DAY"),
    price: float | None = typer.Option(default=None),
    account_id: str | None = typer.Option(default=None),
) -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            resolved_account_id = account_id or await client.resolve_account_id()
            request = OrderRequest.model_validate(
                {
                    "acctId": resolved_account_id,
                    "conid": conid,
                    "side": side.upper(),
                    "quantity": quantity,
                    "orderType": order_type.upper(),
                    "tif": tif.upper(),
                    "price": price,
                }
            )
            preview = await client.preview_order(request)
            _print_json(preview.model_dump(mode="json"))

    _run(_command())


@orders_app.command("place")
def orders_place(
    conid: str,
    side: str,
    quantity: float,
    order_type: str = typer.Option("MKT", "--order-type"),
    tif: str = typer.Option("DAY"),
    price: float | None = typer.Option(default=None),
    account_id: str | None = typer.Option(default=None),
    confirm: bool = typer.Option(False, help="Required to send a live order request."),
) -> None:
    settings = _settings()
    if not confirm:
        raise typer.BadParameter("Pass --confirm to send the order request.")

    async def _command() -> None:
        async with _client(settings) as client:
            resolved_account_id = account_id or await client.resolve_account_id()
            request = OrderRequest.model_validate(
                {
                    "acctId": resolved_account_id,
                    "conid": conid,
                    "side": side.upper(),
                    "quantity": quantity,
                    "orderType": order_type.upper(),
                    "tif": tif.upper(),
                    "price": price,
                }
            )
            placed = await client.place_order(request)
            _print_json(placed.model_dump(mode="json"))

    _run(_command())


@orders_app.command("modify")
def orders_modify(
    order_id: str,
    conid: str,
    side: str,
    quantity: float,
    order_type: str = typer.Option("MKT", "--order-type"),
    tif: str = typer.Option("DAY"),
    price: float | None = typer.Option(default=None),
    account_id: str | None = typer.Option(default=None),
) -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            resolved_account_id = account_id or await client.resolve_account_id()
            request = OrderRequest.model_validate(
                {
                    "acctId": resolved_account_id,
                    "conid": conid,
                    "side": side.upper(),
                    "quantity": quantity,
                    "orderType": order_type.upper(),
                    "tif": tif.upper(),
                    "price": price,
                }
            )
            updated = await client.modify_order(request, order_id)
            _print_json(updated.model_dump(mode="json"))

    _run(_command())


@orders_app.command("cancel")
def orders_cancel(order_id: str, account_id: str | None = typer.Option(default=None)) -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            resolved_account_id = account_id or await client.resolve_account_id()
            result = await client.cancel_order(resolved_account_id, order_id)
            _print_json(result)

    _run(_command())


@orders_app.command("switch-account")
def orders_switch_account(account_id: str) -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            result = await client.switch_account(account_id)
            _print_json(result)

    _run(_command())


@trades_app.command("list")
def trades_list() -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            trades = await client.list_trades()
            _print_json([trade.model_dump(mode="json") for trade in trades])

    _run(_command())


@transactions_app.command("history")
def transactions_history(
    conid: str,
    account_id: str | None = typer.Option(default=None),
    currency: str = typer.Option("USD"),
    days: int | None = typer.Option(default=None),
) -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            history = await client.get_account_transaction_history(
                conid,
                account_id=account_id,
                currency=currency,
                days=days,
            )
            _print_json(history.model_dump(mode="json"))

    _run(_command())


@transactions_app.command("funding")
def transactions_funding(
    conid: str,
    account_id: str | None = typer.Option(default=None),
    currency: str = typer.Option("USD"),
    days: int | None = typer.Option(default=None),
) -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            transactions = await client.list_funding_transactions(
                conid,
                account_id=account_id,
                currency=currency,
                days=days,
            )
            _print_json([transaction.model_dump(mode="json") for transaction in transactions])

    _run(_command())


@scanner_app.command("params")
def scanner_params() -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            params = await client.get_scanner_parameters()
            _print_json(params.model_dump(mode="json"))

    _run(_command())


@scanner_app.command("run")
def scanner_run(
    instrument: str,
    scan_type: str,
    location: str,
) -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            results = await client.run_scanner(
                instrument=instrument,
                scan_type=scan_type,
                location=location,
            )
            _print_json([result.model_dump(mode="json") for result in results])

    _run(_command())


@watchlists_app.command("list")
def watchlists_list() -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            watchlists = await client.list_watchlists()
            _print_json([watchlist.model_dump(mode="json") for watchlist in watchlists])

    _run(_command())


@watchlists_app.command("show")
def watchlists_show(watchlist_id: str) -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            watchlist = await client.get_watchlist(watchlist_id)
            _print_json(watchlist.model_dump(mode="json"))

    _run(_command())


@watchlists_app.command("create")
def watchlists_create(name: str) -> None:
    settings = _settings()

    async def _command() -> None:
        async with _client(settings) as client:
            watchlist = await client.create_watchlist(name)
            _print_json(watchlist.model_dump(mode="json"))

    _run(_command())


@ws_app.command("watch")
def ws_watch(topic: str) -> None:
    settings = _settings()
    logger = get_logger("ib_cli.ws.watch")

    async def _command() -> None:
        async with _client(settings) as client:
            async for message in client.stream_topic(topic):
                logger.info("websocket_message", topic=topic, payload=message)
                _print_json(message)

    _run(_command())


@ws_app.command("market")
def ws_market(conid: str, fields: str = "31,84,86") -> None:
    settings = _settings()
    logger = get_logger("ib_cli.ws.market")

    async def _command() -> None:
        async with _client(settings) as client:
            async for message in client.stream_market_data(conid, fields.split(",")):
                logger.info("market_stream_message", conid=conid, payload=message)
                _print_json(message)

    _run(_command())


@ws_app.command("orders")
def ws_orders() -> None:
    settings = _settings()
    logger = get_logger("ib_cli.ws.orders")

    async def _command() -> None:
        async with _client(settings) as client:
            async for message in client.stream_live_orders():
                logger.info("orders_stream_message", payload=message)
                _print_json(message)

    _run(_command())


@ws_app.command("pnl")
def ws_pnl() -> None:
    settings = _settings()
    logger = get_logger("ib_cli.ws.pnl")

    async def _command() -> None:
        async with _client(settings) as client:
            async for message in client.stream_pnl():
                logger.info("pnl_stream_message", payload=message)
                _print_json(message)

    _run(_command())


@ws_app.command("trades")
def ws_trades() -> None:
    settings = _settings()
    logger = get_logger("ib_cli.ws.trades")

    async def _command() -> None:
        async with _client(settings) as client:
            async for message in client.stream_trades():
                logger.info("trades_stream_message", payload=message)
                _print_json(message)

    _run(_command())


def main() -> None:
    app()


if __name__ == "__main__":
    main()
