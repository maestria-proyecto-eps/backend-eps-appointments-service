import os
from dotenv import load_dotenv
load_dotenv()

import pytest
from datetime import date
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocalOperativa

client = TestClient(app)

ID_PACIENTE_TEST = 1018442903
ID_ESP_TEST = 2
ID_MEDICO_TEST = 80112457

@pytest.fixture(scope="module")
def db_setup():
    yield {
        "date": date(2026, 3, 31),
        "specialty_id": ID_ESP_TEST,
        "patient_id": ID_PACIENTE_TEST
    }

def test_integration_availability_flow(db_setup):
    headers = {"X-Patient-Id": str(db_setup["patient_id"])}
    params = {
        "specialty_id": db_setup["specialty_id"],
        "startDate": db_setup["date"].isoformat(),
        "endDate": db_setup["date"].isoformat(),
        "doctor_id": ID_MEDICO_TEST
    }

    response = client.get("/api/appointments/availability", params=params, headers=headers)

    if response.status_code == 503:
        print("\nError del servidor:", response.text)

    assert response.status_code == 200
    assert len(response.json()) > 0

def test_integration_unauthorized_no_header():
    response = client.get(f"/api/appointments/availability?specialty_id={ID_ESP_TEST}&startDate=2026-03-31&endDate=2026-03-31")
    assert response.status_code in [401, 403]