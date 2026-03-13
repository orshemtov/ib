# AGENTS

## Project layout

- Root package `ib-cli`: Typer CLI entrypoint in `src/ib_cli/main.py`
- Workspace package `ib-client`: typed IBKR Client Portal client in `packages/ib-client/src/ib_client`
- Package metadata for standalone publishing lives in `packages/ib-client/pyproject.toml`
- Package skill prompt lives in `packages/ib-client/SKILL.md`
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
- `uv build packages/ib-client`
- `uv run ib gateway download`
- `uv run ib gateway start`
- `uv run ib auth login`
- `uv run ib market history <conid>`
- `uv run ib options strikes <conid> --month <yyyymm>`
- `uv run ib trades list`
- `uv run ib ws market <conid>`
- `uv run ib ws orders`

## Auth notes

- Individual IBKR gateway auth is only best-effort automated
- Username/password can be filled automatically from env
- 2FA still requires human completion in the browser
- Gateway, browser login, and API calls must run on the same machine
- Gateway is downloaded into `gateway/` via `ib gateway download`
- Repo config defaults the gateway to port `5001` because macOS may reserve `5000`
- Published `ib-client` consumers also default `IB_GATEWAY_DIR` to `./gateway`, relative to the consuming project's working directory

## Test notes

- Unit tests should avoid mocks unless there is a compelling reason
- Integration tests hit the real IB account and must use tolerant smoke assertions
- Integration tests are read-only only; do not place orders from tests
- Any future non-read-only tests should live in `tests/integration-full` and run via `mise run test:integration-full`
- Current read-only integration coverage includes ledger, trades, scanner params/run, market history, option lookup/strikes/contracts, and contract rules

## Logging

- Use `ib_client.logger.configure_logging()`
- Support plaintext and JSON logs
- In plaintext mode, color defaults off when `CI=true`

## Packaging

- `packages/ib-client` must remain installable as a standalone library outside this workspace
- Prefer package-safe defaults over repo-root assumptions in library code
- Keep `packages/ib-client/README.md` accurate for local path, GitHub, and future PyPI installs
- Include publishable metadata in `packages/ib-client/pyproject.toml` when adding package features

## Skill

- `packages/ib-client/SKILL.md` is the reusable agent skill for IBKR Client Portal tasks
- Keep the skill biased toward read-only operations unless the user explicitly requests trading or order placement
- Mention gateway/auth constraints clearly whenever editing the skill
