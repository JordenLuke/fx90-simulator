from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, Response

from ..simulator.reader import Reader
from ..simulator.scenario import ScenarioConfig
from ..simulator.scenario_loader import ScenarioLoader


TEMPLATES_PATH = Path(__file__).with_name("templates")
CONTROL_PANEL_PATH = TEMPLATES_PATH / "test_panel.html"
CONTROL_PANEL_CSS_PATH = TEMPLATES_PATH / "test_panel.css"


def create_test_router(reader: Reader) -> APIRouter:
    api = APIRouter(prefix="/test")
    scenario_loader = ScenarioLoader()

    @api.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def panel():
        return HTMLResponse(CONTROL_PANEL_PATH.read_text(encoding="utf-8"))

    @api.get("/assets/test_panel.css", response_class=Response, include_in_schema=False)
    async def stylesheet():
        return Response(CONTROL_PANEL_CSS_PATH.read_text(encoding="utf-8"), media_type="text/css")

    @api.get("/status")
    async def status():
        return reader.test_status()

    @api.get("/scenarios")
    async def scenarios():
        try:
            return {"scenarios": [scenario.to_dict() for scenario in scenario_loader.list()]}
        except ValueError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @api.put("/scenario")
    async def select_scenario(values: dict):
        try:
            if "name" in values:
                scenario = scenario_loader.get(str(values["name"]))
                if "time_scale" in values:
                    scenario.time_scale = float(values["time_scale"])
                    scenario.validate()
            else:
                scenario = ScenarioConfig.from_dict(values)
            reader.set_scenario(scenario)
        except (KeyError, ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return reader.test_status()

    @api.post("/scenario/start")
    async def start_scenario():
        try:
            await reader.start_scenario()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
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
