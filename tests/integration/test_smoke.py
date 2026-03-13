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


def _ledger_snapshot(ledger: dict[str, dict[str, object]]) -> dict[str, dict[str, object]]:
    selected_keys = [
        "currency",
        "cash_balance",
        "stock_market_value",
        "net_liquidation_value",
        "buying_power",
    ]
    return {
        currency: {key: row[key] for key in selected_keys if key in row}
        for currency, row in ledger.items()
    }


def _trade_snapshot(trade: dict[str, object]) -> dict[str, object]:
    selected_keys = ["execution_id", "symbol", "side", "quantity", "price", "trade_time"]
    return {key: trade[key] for key in selected_keys if key in trade}


def _scanner_snapshot(entry: dict[str, object]) -> dict[str, object]:
    selected_keys = ["symbol", "conid", "company_name", "listing_exchange", "sec_type"]
    return {key: entry[key] for key in selected_keys if key in entry}


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
async def test_ledger_smoke() -> None:
    async with IBClient(load_settings()) as client:
        account_id = await client.resolve_account_id()
        ledger = await client.get_account_ledger(account_id)

    ledger_payload = {
        currency: row.model_dump(exclude_none=True) for currency, row in ledger.items()
    }
    _print_section("ledger", _ledger_snapshot(ledger_payload))
    assert isinstance(ledger, dict)
    assert ledger_payload


@pytest.mark.anyio
async def test_trades_smoke() -> None:
    async with IBClient(load_settings()) as client:
        trades = await client.list_trades()

    trade_payload = [trade.model_dump(exclude_none=True) for trade in trades]
    _print_section("trades", [_trade_snapshot(trade) for trade in trade_payload])
    assert isinstance(trades, list)


@pytest.mark.anyio
async def test_scanner_params_smoke() -> None:
    async with IBClient(load_settings()) as client:
        params = await client.get_scanner_parameters()

    params_payload = params.model_dump(exclude_none=True)
    _print_section(
        "scanner params",
        {
            "instrument_count": len(params_payload.get("instrument_list", [])),
            "scan_type_count": len(params_payload.get("scan_type_list", [])),
            "location_count": len(params_payload.get("location_tree", [])),
            "filter_count": len(params_payload.get("filter_list", [])),
        },
    )
    assert params_payload


@pytest.mark.anyio
async def test_scanner_run_smoke() -> None:
    async with IBClient(load_settings()) as client:
        results = await client.run_scanner("STK", "TOP_PERC_GAIN", "STK.US.MAJOR")

    scanner_payload = [result.model_dump(exclude_none=True) for result in results]
    _print_section("scanner run", [_scanner_snapshot(item) for item in scanner_payload[:10]])
    assert isinstance(results, list)


@pytest.mark.anyio
async def test_market_history_smoke() -> None:
    async with IBClient(load_settings()) as client:
        history = await client.get_historical_data("265598", period="1d", bar="1h")

    history_payload = history.model_dump(exclude_none=True)
    _print_section(
        "market history",
        {
            "symbol": history_payload.get("symbol"),
            "points": history_payload.get("points"),
            "bars": history_payload.get("data", [])[:3],
        },
    )
    assert history.data


@pytest.mark.anyio
async def test_options_lookup_smoke() -> None:
    async with IBClient(load_settings()) as client:
        stocks = await client.lookup_stocks(["AAPL"])
        secdef = await client.get_security_definition(["265598"])
        strikes = await client.get_option_strikes("265598", "OPT", "202604")
        contracts = await client.get_option_contracts("265598", "OPT", "202604", "200", "C")

    stocks_payload = {
        symbol: [item.model_dump(exclude_none=True) for item in items[:2]]
        for symbol, items in stocks.items()
    }
    _print_section("option stock lookup", stocks_payload)
    _print_section("option secdef", [item.model_dump(exclude_none=True) for item in secdef[:2]])
    _print_section("option strikes", strikes.model_dump(exclude_none=True))
    _print_section(
        "option contracts", [item.model_dump(exclude_none=True) for item in contracts[:5]]
    )
    assert stocks.get("AAPL")
    assert secdef
    assert strikes.call or strikes.put
    assert contracts


@pytest.mark.anyio
async def test_contract_rules_smoke() -> None:
    async with IBClient(load_settings()) as client:
        contracts = await client.get_option_contracts("265598", "OPT", "202604", "200", "C")
        conid = str(next(contract.conid for contract in contracts if contract.conid))
        rules = await client.get_contract_rules(conid, exchange="SMART")

    rules_payload = rules.model_dump(exclude_none=True)
    _print_section(
        "contract rules",
        {
            "order_types": rules_payload.get("order_types"),
            "size_increment": rules_payload.get("size_increment"),
            "price_increment": rules_payload.get("price_increment"),
            "tif_types": rules_payload.get("tifTypes"),
        },
    )
    assert rules_payload


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
