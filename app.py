from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from config import settings
from reader import reader
from websocket import manager

app = FastAPI(title="FX90 Simulator", version="0.1.0")


@app.get("/reader/status")
async def get_status():
    return reader.status()


@app.post("/reader/start")
async def start_reader():
    return reader.start()


@app.post("/reader/stop")
async def stop_reader():
    return reader.stop()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await websocket.send_json({
            "type": "status",
            "data": reader.status(),
        })

        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.https_port,
        ssl_keyfile=settings.server_key,
        ssl_certfile=settings.server_cert,
        reload=settings.reload,
    )
