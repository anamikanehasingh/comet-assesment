"""WebSocket entry (JWT query token + channel param)."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from jwt import InvalidTokenError

from app.core.security import decode_token
from app.websockets.manager import hub

router = APIRouter()


@router.websocket("/ws")
async def websocket_connect(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    channel = websocket.query_params.get("channel")
    if not token or not channel:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    try:
        decode_token(token)
    except InvalidTokenError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await hub.connect(channel, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await hub.disconnect(channel, websocket)
