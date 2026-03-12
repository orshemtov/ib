import pytest
from ib_client.client import IBClient
from ib_client.settings import load_settings

pytestmark = [pytest.mark.integration, pytest.mark.real_account]


def _print_section(title: str, payload: object) -> None:
    print(f"\n=== {title} ===")
    print(payload)


def _account_list_snapshot(accounts: list[dict[str, object]]) -> list[dict[str, object]]:
    selected_keys = [
        "account_id",
        "id",
        "account_title",
        "displayName",
        "currency",
        "type",
        "tradingType",
        "brokerageAccess",
    ]
    return [{key: account[key] for key in selected_keys if key in account} for account in accounts]


def _account_snapshot(summary: dict[str, object]) -> dict[str, object]:
    selected_keys = [
        "account_id",
        "account_type",
        "currency",
        "net_liquidation",
        "total_cash_value",
        "availablefunds",
        "buyingpower",
        "excessliquidity",
        "grosspositionvalue",
    ]
    return {key: summary[key] for key in selected_keys if key in summary}


def _position_snapshot(position: dict[str, object]) -> dict[str, object]:
    selected_keys = [
        "contract_desc",
        "description",
        "conid",
        "position",
        "market_price",
        "marketPrice",
        "market_value",
        "marketValue",
        "currency",
        "unrealizedPnl",
        "realizedPnl",
    ]
    return {key: position[key] for key in selected_keys if key in position}


def _pnl_snapshot(row: dict[str, object]) -> dict[str, object]:
    selected_keys = ["account_id", "daily", "unrealized", "realized", "dpl", "upl", "rpl"]
    return {key: row[key] for key in selected_keys if key in row}


@pytest.mark.anyio
async def test_auth_status_smoke() -> None:
    async with IBClient(load_settings()) as client:
        status = await client.get_auth_status()

    _print_section("auth status", status.model_dump(exclude_none=True))
    assert status.authenticated is not None or status.connected is not None


@pytest.mark.anyio
async def test_accounts_smoke() -> None:
    async with IBClient(load_settings()) as client:
        accounts = await client.list_accounts()

    accounts_payload = [account.model_dump(exclude_none=True) for account in accounts]
    _print_section(
        "accounts",
        _account_list_snapshot(accounts_payload),
    )
    assert isinstance(accounts, list)
    assert len(accounts) >= 1
    assert any(account.identifier for account in accounts)


@pytest.mark.anyio
async def test_account_summary_smoke() -> None:
    async with IBClient(load_settings()) as client:
        account_id = await client.resolve_account_id()
        summary = await client.get_account_summary(account_id)

    summary_payload = summary.model_dump(exclude_none=True)
    _print_section("account summary", _account_snapshot(summary_payload))
    assert summary.account_id in {None, account_id}
    assert summary_payload


@pytest.mark.anyio
async def test_account_pnl_smoke() -> None:
    async with IBClient(load_settings()) as client:
        pnl_rows = await client.get_profit_and_loss()

    pnl_payload = [row.model_dump(exclude_none=True) for row in pnl_rows]
    _print_section("account pnl", [_pnl_snapshot(row) for row in pnl_payload])
    assert isinstance(pnl_rows, list)
    for row in pnl_rows:
        assert row.model_dump(exclude_none=True)


@pytest.mark.anyio
async def test_positions_smoke() -> None:
    async with IBClient(load_settings()) as client:
        account_id = await client.resolve_account_id()
        positions = await client.list_positions(account_id)

    positions_payload = [position.model_dump(exclude_none=True) for position in positions]
    _print_section(
        "positions",
        [_position_snapshot(position) for position in positions_payload],
    )
    assert isinstance(positions, list)
    for position in positions:
        assert position.model_dump(exclude_none=True)


@pytest.mark.anyio
async def test_contract_search_smoke() -> None:
    async with IBClient(load_settings()) as client:
        matches = await client.search_contract("AAPL")

    _print_section(
        "contract search",
        [match.model_dump(exclude_none=True) for match in matches[:5]],
    )
    assert isinstance(matches, list)
    assert len(matches) >= 1
    assert any(match.conid for match in matches)


@pytest.mark.anyio
async def test_live_orders_smoke() -> None:
    async with IBClient(load_settings()) as client:
        orders = await client.list_live_orders(force=False)

    _print_section("live orders", orders.model_dump(exclude_none=True))
    assert isinstance(orders.orders, list)
