## ib-client

Reusable typed Interactive Brokers Client Portal API client package.

This package is intended to be installable independently from the CLI workspace and used from another `uv` project.

### Install from a local path

```bash
uv add /absolute/path/to/packages/ib-client
```

### What it provides

- `IBClient` for async HTTP and websocket access
- `Settings` / `load_settings()` for environment-backed configuration
- Pydantic models for common account, market, order, and session payloads
- Shared `structlog` logging setup in `ib_client.logger`

### Basic usage

```python
import asyncio

from ib_client.client import IBClient
from ib_client.settings import Settings


async def main() -> None:
    settings = Settings()
    async with IBClient(settings) as client:
        accounts = await client.list_accounts()
        print([account.identifier for account in accounts])


asyncio.run(main())
```
