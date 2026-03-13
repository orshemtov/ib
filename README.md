## Interactive Brokers Web API CLI

Typed Python workspace for the Interactive Brokers Client Portal Web API.

### Prerequisites

- Python 3.13
- `uv`
- `mise`
- Java 8u192 or newer for the IBKR Client Portal Gateway
- A funded IBKR Pro account

### Workspace layout

- `src/ib_cli/main.py`: Typer CLI
- `packages/ib-client/src/ib_client`: reusable API client
- `tests/unit`: pure unit tests
- `tests/integration`: real-account smoke tests

### Setup

1. Copy `.env.example` to `.env`
2. Set `IB_USERNAME`, `IB_PASSWORD`, and optionally `IB_ACCOUNT_ID`
3. Download the gateway with `uv run ib gateway download`
4. Run `mise run sync`
5. If port `5000` is occupied on your machine, this repo defaults the gateway to `5001`

### Install as a tool

- From a local checkout with `mise`: `mise run install`
- Refresh the global install from the current local checkout: `mise run upgrade`
- Run once from a local checkout: `uv tool install .`
- Then use the CLI directly as `ib`
- One-off execution also works with `uvx --from . ib --help`
- After publishing, the same `uv tool install <package>` and `uvx <package>` workflow applies

### Common commands

- `uv run ib gateway download`
- `uv run ib gateway start`
- `uv run ib auth login`
- `uv run ib auth status`
- `uv run ib accounts list`
- `uv run ib accounts summary`
- `uv run ib accounts pnl`
- `uv run ib portfolio ledger`
- `uv run ib portfolio combos`
- `uv run ib positions list`
- `uv run ib market search AAPL`
- `uv run ib market quote 265598`
- `uv run ib market history 265598 --period 1d --bar 1h`
- `uv run ib options stocks AAPL`
- `uv run ib options strikes 265598 --month 202504`
- `uv run ib options contracts 265598 202504 200 C`
- `uv run ib options rules 265598`
- `uv run ib fx pairs USD`
- `uv run ib fx rate --source ILS --target USD`
- `uv run ib fx preview --source ILS --target USD --amount 1000`
- `uv run ib fx preview --source USD --target ILS --amount 1000`
- `uv run ib fx preview-close-to-usd ILS`
- `uv run ib orders list`
- `uv run ib orders status 123456789`
- `uv run ib orders cancel 123456789`
- `uv run ib trades list`
- `uv run ib transactions history 265598 --days 30`
- `uv run ib transactions funding 265598 --days 30`
- `uv run ib scanner params`
- `uv run ib scanner run STK TOP_PERC_GAIN STK.US.MAJOR`
- `uv run ib watchlists list`
- `uv run ib ws market 265598`
- `uv run ib ws orders`
- `uv run ib ws pnl`
- `uv run ib ws trades`

### Logging

- `IB_LOG_FORMAT=plain|json`
- `IB_LOG_COLOR=auto|true|false`
- plaintext color auto-disables when `CI=true`

### Testing

- Unit tests: `mise run test`
- Integration smoke tests: `mise run test:integration` (`pytest -s -vv tests/integration`)
- Reserved non-read-only integration tests: `mise run test:integration-full`
- Full suite: `mise run test:all`

Integration tests use tolerant assertions because balances, positions, and market data change over time, and they print the read-only payloads they receive for easier inspection.
Non-read-only tests should live under `tests/integration-full` and stay out of the default integration suite.

### Notes

- Gateway auth is best-effort assisted, not fully automated
- 2FA is still manual
- The gateway uses a local self-signed certificate by default
- The downloaded gateway config lives at `gateway/root/conf.yaml`
- `ib gateway download` skips the download when the local archive already matches the latest remote metadata
- A single IB username can only hold one brokerage session at a time

### Newly supported API areas

- Options discovery: stock lookup, security definitions, strikes, option contracts, contract rules
- Historical data: bar history via `market history`
- Portfolio detail: ledger and combo positions
- Order lifecycle: status, modify, cancel, account switch
- Trades/executions: recent trades listing
- FX conversion: pairs, rates, preview/place conversion, close positive balances to USD
- Read-only transaction history: PortfolioAnalyst transaction visibility plus funding-like filtering
- Market discovery: scanner params and scanner runs
- Watchlists: list, show, create
- Typed websocket helpers: market data, live orders, PnL, and trades streams
