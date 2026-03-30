import pytest
from datetime import date, timedelta, time
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from app.main import app
from app.db.session import get_db_admin, get_db_operativa
from app.models.minimal_models import Especialidad, Usuario, Doctor, Agenda, BaseAdmin, BaseOperativa
from app.routers.appointments import get_authenticated_patient_id

# 1. Motores SQLite en Memoria
engine_test_admin = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
engine_test_operativa = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

TestingSessionAdmin = sessionmaker(autocommit=False, autoflush=False, bind=engine_test_admin)
TestingSessionOperativa = sessionmaker(autocommit=False, autoflush=False, bind=engine_test_operativa)

# 2. Overrides de Dependencias
def override_get_db_admin():
    db = TestingSessionAdmin()
    try: yield db
    finally: db.close()

def override_get_db_operativa():
    db = TestingSessionOperativa()
    try: yield db
    finally: db.close()

def override_get_authenticated_patient_id():
    return 100 # ID del paciente para el test

app.dependency_overrides[get_db_admin] = override_get_db_admin
app.dependency_overrides[get_db_operativa] = override_get_db_operativa
app.dependency_overrides[get_authenticated_patient_id] = override_get_authenticated_patient_id

client = TestClient(app)

# 3. Fixture para Setup de Datos
@pytest.fixture(autouse=True)
def setup_mock_dbs():
    BaseAdmin.metadata.create_all(bind=engine_test_admin)
    BaseOperativa.metadata.create_all(bind=engine_test_operativa)

    db_admin = TestingSessionAdmin()
    db_op = TestingSessionOperativa()

    try:
        # Especialidad que REQUIERE remisión
        esp = Especialidad(id_especialidad=2, nombre_especialidad="Cardiologia", requiere_remision=True)
        usr = Usuario(id_usuario=20, estado=True)
        doc = Doctor(id_medico=50, id_usuario=20, id_especialidad=2, nombre="Mock", apellido="Doc")
        db_admin.add_all([esp, usr, doc])
        db_admin.commit()

        tomorrow = date.today() + timedelta(days=1)
        agenda = Agenda(
            id_agenda=10, id_doctor=50, id_especialidad=2,
            fecha=tomorrow, hora_inicio=time(9, 0), hora_fin=time(9, 30), estado=1
        )
        db_op.add(agenda)
        db_op.commit()
    finally:
        db_admin.close()
        db_op.close()

    yield
    BaseAdmin.metadata.drop_all(bind=engine_test_admin)
    BaseOperativa.metadata.drop_all(bind=engine_test_operativa)

# 4. El Test Unitario
def test_unit_availability_remission_required_forbidden():
    """
    Simula que el service lanza el error 403 de remisión.
    """
    tomorrow = date.today() + timedelta(days=1)
    params = {
        "specialty_id": 2,
        "startDate": str(tomorrow),
        "endDate": str(tomorrow)
    }

    # Mockea la función del SERVICE que el router llama
    with patch("app.routers.appointments.get_availability_slots") as mock_service:
        # Simulamos exactamente el error que lanzaría tu lógica de negocio
        mock_service.side_effect = HTTPException(
            status_code=403,
            detail="Paciente no cuenta con remision vigente para esta especialidad"
        )

        response = client.get("/api/appointments/availability", params=params)

        assert response.status_code == 403
        assert "remision" in response.json()["detail"].lower()

@pytest.fixture(scope="module", autouse=True)
def cleanup_overrides():
    yield
    app.dependency_overrides.clear()