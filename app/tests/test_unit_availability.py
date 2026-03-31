import pytest
from datetime import date, timedelta, time
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.session import get_db_admin, get_db_operativa
from app.models.minimal_models import Especialidad, Persona, Doctor, Agenda, BaseAdmin, BaseOperativa, Usuario, Role
from app.routers.appointments import get_authenticated_patient_id

# Configuración de Motores SQLite en memoria con StaticPool para persistencia entre sesiones
engine_admin = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
engine_operativa = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

TestingSessionAdmin = sessionmaker(bind=engine_admin)
TestingSessionOperativa = sessionmaker(bind=engine_operativa)

# Datos de prueba
MOCK_PACIENTE_DOC = 1018442903
MOCK_MEDICO_DOC = 80112457

# Overrides de dependencias
app.dependency_overrides[get_db_admin] = lambda: TestingSessionAdmin()
app.dependency_overrides[get_db_operativa] = lambda: TestingSessionOperativa()
app.dependency_overrides[get_authenticated_patient_id] = lambda: MOCK_PACIENTE_DOC

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_dbs():
    # Crea las tablas en el orden correcto
    BaseAdmin.metadata.create_all(bind=engine_admin)
    BaseOperativa.metadata.create_all(bind=engine_operativa)

    db_a = TestingSessionAdmin()
    db_o = TestingSessionOperativa()

    try:
        # 1. Crear Rol (Necesario para la FK de Usuario)
        rol = Role(id_rol=2, nombre_rol="Paciente")
        db_a.add(rol)
        db_a.flush()

        # 2. Crear Persona y Especialidad
        persona = Persona(num_documento=MOCK_MEDICO_DOC, nombres="Doc", apellidos="Prueba")
        esp = Especialidad(id_especialidad=2, nombre_especialidad="Cardiologia", requiere_remision=True)
        db_a.add_all([persona, esp])
        db_a.flush()

        # 3. Crear Usuario y Doctor vinculado a la Persona
        usr = Usuario(id_usuario=1, num_documento=MOCK_MEDICO_DOC, password="...", id_rol=2, estado=True)
        doc = Doctor(id_medico=MOCK_MEDICO_DOC, num_licencia=123, id_especialidad=2)
        db_a.add_all([usr, doc])
        db_a.commit()

        # 4. Crear Agenda en Base Operativa
        tomorrow = date.today() + timedelta(days=1)
        agenda = Agenda(
            id_agenda=1, id_doctor=MOCK_MEDICO_DOC, id_especialidad=2,
            fecha=tomorrow, hora_inicio=time(8, 0), hora_fin=time(8, 30), estado=1
        )
        db_o.add(agenda)
        db_o.commit()
    finally:
        db_a.close()
        db_o.close()

    yield
    BaseAdmin.metadata.drop_all(bind=engine_admin)
    BaseOperativa.metadata.drop_all(bind=engine_operativa)

def test_unit_forbidden_no_remission():
    tomorrow = date.today() + timedelta(days=1)

    response = client.get(
        f"/api/appointments/availability?specialty_id=2&startDate={tomorrow}&endDate={tomorrow}"
    )

    # Imprimimos el detalle si falla para saber POR QUÉ dio 404
    if response.status_code == 404:
        print(f"\nDEBUG 404: {response.json()}")

    assert response.status_code == 403