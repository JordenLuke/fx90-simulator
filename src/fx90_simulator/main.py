import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .api.rest import create_router
from .api.websocket import WebSocketManager, register_endpoint
from .simulator.reader import Reader


def create_app() -> FastAPI:
    app = FastAPI(title="FX90 Simulator")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    reader = Reader()
    websocket_manager = WebSocketManager()
    app.include_router(create_router(reader))
    register_endpoint(app, reader, websocket_manager)

    @app.on_event("startup")
    async def startup() -> None:
        if config.AUTO_START:
            await reader.start()

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=config.HOST,
        port=config.HTTPS_PORT,
        ssl_certfile=str(config.CERT_FILE),
        ssl_keyfile=str(config.KEY_FILE),
    )
