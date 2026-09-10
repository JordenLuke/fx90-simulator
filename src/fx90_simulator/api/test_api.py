from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from ..simulator.reader import Reader


CONTROL_PANEL_PATH = Path(__file__).with_name("templates") / "test_panel.html"


def create_test_router(reader: Reader) -> APIRouter:
    api = APIRouter(prefix="/test")

    @api.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def panel():
        return HTMLResponse(CONTROL_PANEL_PATH.read_text(encoding="utf-8"))

    @api.get("/status")
    async def status():
        return reader.test_status()

    @api.put("/config")
    async def update_config(values: dict):
        try:
            reader.update_test_config(values)
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return reader.test_status()

    @api.post("/start")
    async def start():
        try:
            await reader.start()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return reader.test_status()

    @api.post("/stop")
    async def stop():
        await reader.stop()
        return reader.test_status()

    @api.post("/reset")
    async def reset():
        await reader.reset()
        return reader.test_status()

    return api
