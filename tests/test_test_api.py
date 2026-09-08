import pytest
from fastapi.testclient import TestClient

from fx90_simulator.main import create_app


@pytest.mark.integration
def test_control_panel_and_status() -> None:
    with TestClient(create_app()) as client:
        panel = client.get("/test/")
        status = client.get("/test/status")

    assert panel.status_code == 200
    assert "FX90 Simulator" in panel.text
    assert status.status_code == 200
    assert status.json()["config"]["runner_count"] == 400


@pytest.mark.integration
def test_control_api_rejects_invalid_settings() -> None:
    with TestClient(create_app()) as client:
        response = client.put("/test/config", json={"noise_percent": 101})

    assert response.status_code == 400
