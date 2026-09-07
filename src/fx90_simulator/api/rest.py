import base64

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse, Response

from .. import config
from ..simulator.reader import Reader

router = APIRouter()


def require_bearer(authorization: str | None) -> None:
    if authorization != f"Bearer {config.BEARER_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/cloud/localRestLogin")
async def login(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Basic "):
        raise HTTPException(status_code=401, detail="Basic authentication required")
    try:
        username, password = base64.b64decode(authorization[6:]).decode().split(":", 1)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid Basic authentication") from exc
    if username != config.USERNAME or password != config.PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"message": config.BEARER_TOKEN}


def create_router(reader: Reader) -> APIRouter:
    api = APIRouter()

    @api.get("/cloud/status")
    async def status(authorization: str | None = Header(default=None)):
        require_bearer(authorization)
        return reader.status()

    @api.get("/cloud/mode")
    async def mode(authorization: str | None = Header(default=None)):
        require_bearer(authorization)
        return reader.mode()

    @api.put("/cloud/mode")
    async def set_mode(
        request: Request,
        authorization: str | None = Header(default=None),
    ):
        require_bearer(authorization)
        return Response(status_code=204)

    @api.put("/cloud/start")
    async def start(
        request: Request,
        authorization: str | None = Header(default=None),
    ):
        require_bearer(authorization)
        if reader.radio_active:
            return JSONResponse(status_code=422, content={"message": "start currently ongoing"})
        await reader.start()
        return Response(status_code=204)

    @api.put("/cloud/stop")
    async def stop(authorization: str | None = Header(default=None)):
        require_bearer(authorization)
        await reader.stop()
        return Response(status_code=204)

    return api
