from fastapi import WebSocket, WebSocketDisconnect

from ..simulator.reader import Reader


class WebSocketManager:
    """Tracks active FXR90 WebSocket connections."""

    def __init__(self) -> None:
        self.connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.connections.discard(websocket)


def register_endpoint(app, reader: Reader, manager: WebSocketManager) -> None:
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await manager.connect(websocket)

        async def sender(message: str) -> None:
            await websocket.send_text(message)

        reader.register_sender(sender)
        try:
            while True:
                await websocket.receive()
        except WebSocketDisconnect:
            pass
        finally:
            reader.unregister_sender(sender)
            manager.disconnect(websocket)
