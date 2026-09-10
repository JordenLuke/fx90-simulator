from contextlib import asynccontextmanager
import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .api.rest import create_router
from .api.test_api import create_test_router
from .api.websocket import WebSocketManager, register_endpoint
from .simulator.reader import Reader

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def create_app() -> FastAPI:
    reader = Reader()
    websocket_manager = WebSocketManager()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if config.AUTO_START:
            await reader.start()
        try:
            yield
        finally:
            await reader.stop()

    app = FastAPI(title="FX90 Simulator", lifespan=lifespan)
    if config.CORS_ORIGINS:
        app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])

    app.include_router(create_router(reader))
    app.include_router(create_test_router(reader))
    register_endpoint(app, reader, websocket_manager)
    return app


app = create_app()


def main() -> None:
    uvicorn.run(app, host=config.HOST, port=config.HTTPS_PORT, ssl_certfile=str(config.CERT_FILE), ssl_keyfile=str(config.KEY_FILE))


if __name__ == "__main__":
    main()
