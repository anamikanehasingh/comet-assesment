"""In-process WebSocket hub (single node MVP); scale-out via Redis pub/sub per LLD."""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from typing import Any
from uuid import UUID

from fastapi import WebSocket


class WebSocketHub:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._channels: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, channel: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._channels[channel].add(websocket)

    async def disconnect(self, channel: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._channels[channel].discard(websocket)
            if not self._channels[channel]:
                del self._channels[channel]

    async def broadcast(self, channel: str, message: dict[str, Any]) -> None:
        body = json.dumps(message, default=str)
        async with self._lock:
            targets = list(self._channels.get(channel, set()))
        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_text(body)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(channel, ws)

    @staticmethod
    def ride_channel(ride_id: UUID) -> str:
        return f"ride:{ride_id}"

    @staticmethod
    def driver_channel(driver_id: UUID) -> str:
        return f"driver:{driver_id}"


hub = WebSocketHub()
