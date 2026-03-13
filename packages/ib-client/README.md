## ib-client

Typed async Python client for the Interactive Brokers Client Portal Web API.

### Features

- Async HTTP client for account, portfolio, market data, FX conversion, options, orders, trades, scanners, watchlists, and read-only transaction history
- Built-in websocket helpers for market data, live orders, PnL, and trades streams
- Gateway download and startup helpers for the local IBKR Client Portal Gateway
- Playwright-assisted login workflow with typed results and manual 2FA handoff
- Pydantic models for common IBKR request and response payloads

### Pre-requisites

- Python 3.13+
- A local Interactive Brokers Client Portal Gateway installation or permission to download it
- A funded IBKR account with Client Portal API access
- Java 8u192 or newer when running the local gateway

### Installation

From PyPI after publishing:

```bash
uv add ib-client
```

From GitHub:

```bash
uv add git+https://github.com/orshemtov/ib#subdirectory=packages/ib-client
```

From a local checkout:

```bash
uv add /absolute/path/to/packages/ib-client
```

Basic usage:

```python
import asyncio

from ib_client import IBClient


async def main() -> None:
    async with IBClient() as client:
        accounts = await client.list_accounts()
        print([account.identifier for account in accounts])


asyncio.run(main())
```

Login workflow:

```python
import asyncio

from ib_client import AuthWorkflow


async def main() -> None:
    result = await AuthWorkflow(username="your-username", password="your-password").login()
    print(result.model_dump(mode="json"))


asyncio.run(main())
```

FX conversion preview:

```python
import asyncio

from ib_client import IBClient


async def main() -> None:
    async with IBClient() as client:
        pair, request = await client.build_fx_conversion_request(
            "ILS",
            "USD",
            1000,
        )
        preview = await client.preview_fx_conversion(request)
        print(pair.model_dump(mode="json"))
        print(preview.model_dump(mode="json"))


asyncio.run(main())
```

Close a positive non-USD cash balance into USD:

```python
import asyncio

from ib_client import IBClient


async def main() -> None:
    async with IBClient() as client:
        preview = await client.preview_close_to_usd("ILS")
        print(preview.model_dump(mode="json"))


asyncio.run(main())
```

Transaction history visibility:

```python
import asyncio

from ib_client import IBClient


async def main() -> None:
    async with IBClient() as client:
        history = await client.get_account_transaction_history("265598", days=30)
        print(history.model_dump(mode="json"))


asyncio.run(main())
```

CLI examples:

```bash
uv run ib fx pairs USD
uv run ib fx rate --source ILS --target USD
uv run ib fx preview --source ILS --target USD --amount 1000
uv run ib fx place --source ILS --target USD --amount 1000 --confirm
uv run ib fx preview-close-to-usd ILS
uv run ib transactions history 265598 --days 30
uv run ib transactions funding 265598 --days 30
```

Environment variables:

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `IB_USERNAME` | No | - | Username for browser-assisted login |
| `IB_PASSWORD` | No | - | Password for browser-assisted login |
| `IB_ACCOUNT_ID` | No | - | Preferred brokerage account ID |
| `IB_GATEWAY_DIR` | No | `./gateway` | Local gateway install directory |
| `IB_GATEWAY_CONFIG_PATH` | No | `./gateway/root/conf.yaml` when needed | Override gateway config path |
| `IB_API_HOST` | No | `localhost` | Gateway host |
| `IB_API_PORT` | No | `5001` | Gateway port |
| `IB_USE_SSL` | No | `true` | Use HTTPS/WSS when talking to the gateway |
| `IB_VERIFY_SSL` | No | `false` | Verify the gateway certificate |
| `IB_REQUEST_TIMEOUT_SECONDS` | No | `30` | HTTP request timeout |
| `IB_TICKLE_INTERVAL_SECONDS` | No | `60` | Session keepalive interval |
| `IB_PLAYWRIGHT_HEADLESS` | No | `false` | Run login browser headlessly |
| `IB_PLAYWRIGHT_TIMEOUT_SECONDS` | No | `180` | Authentication wait timeout |
| `IB_LOG_LEVEL` | No | `INFO` | Log level |
| `IB_LOG_FORMAT` | No | `plain` | `plain` or `json` logging |
| `IB_LOG_COLOR` | No | `auto` | `auto`, `true`, or `false` for plaintext logs |

### Notes

- `IBClient`, `AuthWorkflow`, and `GatewayManager` accept raw keyword arguments directly; package consumers do not need to instantiate internal settings objects.
- IBKR login is only partially automated. Username and password can be filled for you, but 2FA still requires a human in the browser.
- The gateway, browser login, and API calls must run on the same machine.
- The package defaults to port `5001` because `5000` is commonly reserved on macOS.
- SSL verification is disabled by default because the local gateway usually serves a self-signed certificate.
- Order-related endpoints exist, but read-only flows are the safest default unless you explicitly intend to trade.
- FX conversion uses `/iserver` endpoints and therefore requires an authenticated brokerage session.
- `get_account_transaction_history()` and `transactions funding` are read-only visibility helpers built on `/pa/transactions`; they may surface transfers or funding-like rows, but they are not a guaranteed full funding ledger.
- A common cash-management pattern is to sell `ILS` and buy `USD` after deposits, then sell `USD` and buy `ILS` before withdrawals. `build_fx_conversion_request("ILS", "USD", amount)` and `build_fx_conversion_request("USD", "ILS", amount)` now infer the correct side from the resolved pair symbol.
