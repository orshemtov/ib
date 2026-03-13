---
name: ib-client
description: Use this skill whenever the user is working with Interactive Brokers, IBKR, the Client Portal Web API, the local Client Portal Gateway, conids, contract lookup, market history, scanners, watchlists, account or portfolio data, or websocket market/order/PnL/trade streams. Also use it when the user wants Python code, scripts, tests, troubleshooting, or automation built on top of the `ib-client` package or an IBKR Client Portal integration, even if they do not mention the package name directly.
---

# ib-client

Use this skill to work effectively with the `ib-client` Python package and the Interactive Brokers Client Portal Web API across OpenCode, Claude Code, Codex, Cursor, and other skills-compatible coding agents.

## Goals

- Produce working code that uses the existing typed client instead of hand-rolling raw HTTP requests.
- Respect the gateway and authentication constraints so examples match how IBKR actually works in practice.
- Default to read-only workflows unless the user explicitly asks to preview, place, modify, or cancel orders.
- Favor public package entrypoints and package-safe defaults so guidance works outside this repository too.

## Start here

1. Identify whether the user wants library code, CLI usage, tests, debugging help, or a workflow explanation.
2. Prefer the typed public surface in `IBClient`, `AuthWorkflow`, `GatewayManager`, and the shipped Pydantic models.
3. Instantiate `IBClient`, `AuthWorkflow`, and `GatewayManager` with raw keyword arguments such as `username`, `password`, `gateway_dir`, `api_host`, and `api_port` instead of telling package users to construct internal settings objects.
4. If the task touches auth or gateway startup, account for browser-based 2FA, the same-machine requirement, and the local self-signed certificate.

## Public entrypoints

- `ib_client.IBClient`: main async API surface for HTTP endpoints and websocket helpers
- `ib_client.AuthWorkflow`: login flow with Playwright and manual 2FA handoff
- `ib_client.GatewayManager`: gateway download, configuration, startup, and reachability helpers
- `ib_client.models.*`: typed request and response models for account, market, options, orders, scanners, and watchlists

## If working in this repository

- `packages/ib-client/src/ib_client`: reusable client package source
- `src/ib_cli/main.py`: CLI examples built on top of the package
- `tests/unit`: pure logic tests
- `tests/integration`: read-only smoke tests against a real authenticated session

## Working rules

### Configuration

- For package users, prefer constructor kwargs first and mention `IB_` environment variables only as an optional configuration path.
- `IB_GATEWAY_DIR` defaults to `./gateway` relative to the consuming project's working directory.
- The gateway commonly defaults to port `5001` because macOS may reserve `5000`.

### Authentication and gateway

- The gateway, browser login, and API calls must run on the same machine.
- Username and password can be filled automatically when present.
- 2FA is still manual; say that plainly when generating instructions.
- SSL verification is often disabled against the local gateway because it uses a self-signed certificate.

### Safety

- Prefer read-only account, market, option, scanner, portfolio, and websocket tasks.
- Do not propose order placement by default.
- If the user asks for trading flows, use the existing order request and reply helpers and clearly separate preview from placement.

## Implementation patterns

### Basic client script

```python
import asyncio

from ib_client import IBClient


async def main() -> None:
    async with IBClient() as client:
        accounts = await client.list_accounts()
        print([account.identifier for account in accounts])


asyncio.run(main())
```

### Login script

```python
import asyncio

from ib_client import AuthWorkflow


async def main() -> None:
    result = await AuthWorkflow(username="your-username", password="your-password").login()
    print(result.model_dump(mode="json"))


asyncio.run(main())
```

### Gateway startup

```python
from ib_client import GatewayManager


manager = GatewayManager(gateway_dir="./gateway", api_port=5001)
manager.download_latest()
manager.start()
```

### Resolve account automatically

- Use `await client.resolve_account_id()` when the task needs an account ID and the user did not provide one.

### Market and option lookup

- Use `search_contract()` for symbol lookup.
- Use `lookup_stocks()`, `get_security_definition()`, `get_option_strikes()`, `get_option_contracts()`, and `get_contract_rules()` for options workflows.
- Keep examples explicit about `conid`, month format, strike, and right.

### Streaming

- Use `stream_market_data()`, `stream_live_orders()`, `stream_pnl()`, or `stream_trades()` instead of constructing websocket topics manually unless the task needs a custom topic.

### Tests

- Unit tests should stay focused and avoid mocks unless there is a strong reason.
- Integration tests are read-only smoke tests against a real authenticated IBKR session.
- Put any future non-read-only integration coverage under `tests/integration-full`.

## Common command equivalents

- Download gateway: `uv run ib gateway download`
- Start gateway: `uv run ib gateway start`
- Log in: `uv run ib auth login`
- Fetch market history: `uv run ib market history <conid>`
- Fetch option strikes: `uv run ib options strikes <conid> --month <yyyymm>`
- Stream market data: `uv run ib ws market <conid>`

## Response shape

When producing code or implementation guidance:

1. Say which existing `ib-client` entrypoints you are using.
2. Mention any auth or gateway prerequisites that can block the workflow.
3. Keep examples async and typed, and use raw kwargs for the public constructors.
4. Avoid telling package consumers to place a `.env` file inside an installed package environment.
5. If the task is operational inside this workspace, include the most relevant `uv run ib ...` command as a quick verify step.
6. If the user is not in this repository, keep the guidance package-oriented rather than repo-oriented.

## Common user intents

- "Fetch my account summary" -> `resolve_account_id()` then `get_account_summary()`
- "Look up option chains or strikes" -> stock lookup, security definition, then strikes/contracts helpers
- "Start or download the gateway" -> `GatewayManager.download_latest()` or `GatewayManager.start()`
- "Log in to IBKR" -> `AuthWorkflow(username=..., password=...).login()` with a note that 2FA is manual
- "Stream live market data" -> `stream_market_data()` with conid and fields
- "Build a smoke test" -> prefer tolerant assertions against real read-only payloads
