from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from websockets.asyncio.client import connect

from ib_client.exceptions import WebsocketError
from ib_client.logger import get_logger
from ib_client.models.session import TickleResponse
from ib_client.settings import Settings


class WebsocketClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.logger = get_logger("ib_client.websocket")

    async def stream(self, session: TickleResponse, topic: str) -> AsyncIterator[dict[str, Any]]:
        if not session.session:
            raise WebsocketError("Session token is required before opening a websocket")

        async with connect(
            self.settings.websocket_url,
            additional_headers={"Cookie": f"api={session.session}"},
        ) as websocket:
            await websocket.send(topic)
            self.logger.info("websocket_topic_sent", topic=topic)
            async for raw_message in websocket:
                if isinstance(raw_message, bytes):
                    raw_message = raw_message.decode("utf-8")
                try:
                    yield json.loads(raw_message)
                except json.JSONDecodeError:
                    yield {"message": raw_message}
