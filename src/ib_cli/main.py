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
from ib_client.settings import Settings, load_settings

app = typer.Typer(help="Interactive Brokers Client Portal CLI")
auth_app = typer.Typer(help="Authentication and gateway commands")
gateway_app = typer.Typer(help="Gateway lifecycle and download commands")
accounts_app = typer.Typer(help="Account commands")
positions_app = typer.Typer(help="Position commands")
market_app = typer.Typer(help="Market data commands")
orders_app = typer.Typer(help="Order commands")
ws_app = typer.Typer(help="Websocket commands")

app.add_typer(auth_app, name="auth")
app.add_typer(gateway_app, name="gateway")
app.add_typer(accounts_app, name="accounts")
app.add_typer(positions_app, name="positions")
app.add_typer(market_app, name="market")
app.add_typer(orders_app, name="orders")
app.add_typer(ws_app, name="ws")


def _settings() -> Settings:
    settings = load_settings()
    configure_logging(settings)
    return settings


def _print_json(data: Any) -> None:
    typer.echo(json.dumps(data, indent=2, default=str))


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


@app.callback()
def cli() -> None:
    """Run the Interactive Brokers CLI."""


@auth_app.command("status")
def auth_status() -> None:
    settings = _settings()
    logger = get_logger("ib_cli.auth.status")

    async def _command() -> None:
        async with IBClient(settings) as client:
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
    workflow = AuthWorkflow(settings)
    result = _run(workflow.login())
    _print_json(result.model_dump(mode="json"))


@auth_app.command("start-gateway")
def start_gateway() -> None:
    settings = _settings()
    manager = GatewayManager(settings)
    result = manager.start()
    _print_json(result.model_dump(mode="json"))


@gateway_app.command("download")
def gateway_download(
    beta: bool = typer.Option(False, help="Download the beta gateway build."),
) -> None:
    settings = _settings()
    manager = GatewayManager(settings)
    result = manager.download_latest(beta=beta)
    _print_json(result.model_dump(mode="json"))


@gateway_app.command("start")
def gateway_start() -> None:
    start_gateway()


@accounts_app.command("list")
def accounts_list() -> None:
    settings = _settings()

    async def _command() -> None:
        async with IBClient(settings) as client:
            accounts = await client.list_accounts()
            _print_json([account.model_dump(mode="json") for account in accounts])

    _run(_command())


@accounts_app.command("summary")
def accounts_summary(account_id: str | None = typer.Argument(default=None)) -> None:
    settings = _settings()

    async def _command() -> None:
        async with IBClient(settings) as client:
            resolved_account_id = account_id or await client.resolve_account_id()
            summary = await client.get_account_summary(resolved_account_id)
            _print_json(summary.model_dump(mode="json"))

    _run(_command())


@accounts_app.command("pnl")
def accounts_pnl() -> None:
    settings = _settings()

    async def _command() -> None:
        async with IBClient(settings) as client:
            pnl_rows = await client.get_profit_and_loss()
            _print_json([row.model_dump(mode="json") for row in pnl_rows])

    _run(_command())


@positions_app.command("list")
def positions_list(account_id: str | None = typer.Argument(default=None)) -> None:
    settings = _settings()

    async def _command() -> None:
        async with IBClient(settings) as client:
            resolved_account_id = account_id or await client.resolve_account_id()
            positions = await client.list_positions(resolved_account_id)
            _print_json([position.model_dump(mode="json") for position in positions])

    _run(_command())


@orders_app.command("reply")
def orders_reply(reply_id: str, confirm: bool = typer.Option(True)) -> None:
    settings = _settings()

    async def _command() -> None:
        async with IBClient(settings) as client:
            reply = await client.reply_to_order_prompt(reply_id, confirmed=confirm)
            _print_json(reply.model_dump(mode="json"))

    _run(_command())


@market_app.command("search")
def market_search(symbol: str) -> None:
    settings = _settings()

    async def _command() -> None:
        async with IBClient(settings) as client:
            results = await client.search_contract(symbol)
            _print_json([result.model_dump(mode="json") for result in results])

    _run(_command())


@market_app.command("quote")
def market_quote(conids: list[str], fields: str = "31,55,84,86") -> None:
    settings = _settings()

    async def _command() -> None:
        async with IBClient(settings) as client:
            snapshots = await client.get_market_snapshot(conids=conids, fields=fields.split(","))
            _print_json([snapshot.model_dump(mode="json") for snapshot in snapshots])

    _run(_command())


@orders_app.command("list")
def orders_list(force: bool = False) -> None:
    settings = _settings()

    async def _command() -> None:
        async with IBClient(settings) as client:
            orders = await client.list_live_orders(force=force)
            _print_json(orders.model_dump(mode="json"))

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
        async with IBClient(settings) as client:
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
        async with IBClient(settings) as client:
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


@ws_app.command("watch")
def ws_watch(topic: str) -> None:
    settings = _settings()
    logger = get_logger("ib_cli.ws.watch")

    async def _command() -> None:
        async with IBClient(settings) as client:
            async for message in client.stream_topic(topic):
                logger.info("websocket_message", topic=topic, payload=message)
                _print_json(message)

    _run(_command())


def main() -> None:
    app()


if __name__ == "__main__":
    main()
