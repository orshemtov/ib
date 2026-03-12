# AGENTS

## Project layout

- Root package `ib-cli`: Typer CLI entrypoint in `src/ib_cli/main.py`
- Workspace package `ib-client`: typed IBKR Client Portal client in `packages/ib-client/src/ib_client`
- Tests: `tests/unit` for pure logic, `tests/integration` for real gateway/account smoke tests

## Stack

- Python 3.13 managed with `uv`
- Pydantic and `pydantic-settings` for models and config
- Typer for CLI
- `structlog` for logging via `ib_client/logger.py`
- `pytest` for tests
- `ruff` for lint/format
- `ty` for type checking
- `mise` for task orchestration

## Commands

- `mise run sync`
- `mise run fmt`
- `mise run lint`
- `mise run typecheck`
- `mise run test`
- `mise run test:integration`
- `mise run test:integration-full`
- `mise run test:all`
- `uv run ib gateway download`
- `uv run ib gateway start`
- `uv run ib auth login`

## Auth notes

- Individual IBKR gateway auth is only best-effort automated
- Username/password can be filled automatically from env
- 2FA still requires human completion in the browser
- Gateway, browser login, and API calls must run on the same machine
- Gateway is downloaded into `gateway/` via `ib gateway download`
- Repo config defaults the gateway to port `5001` because macOS may reserve `5000`

## Test notes

- Unit tests should avoid mocks unless there is a compelling reason
- Integration tests hit the real IB account and must use tolerant smoke assertions
- Integration tests are read-only only; do not place orders from tests
- Any future non-read-only tests should live in `tests/integration-full` and run via `mise run test:integration-full`

## Logging

- Use `ib_client.logger.configure_logging()`
- Support plaintext and JSON logs
- In plaintext mode, color defaults off when `CI=true`
