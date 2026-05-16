from pathlib import Path
import pytest
from datetime import date, time

from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool, text
from sqlalchemy.orm import sessionmaker


load_dotenv(Path(__file__).resolve().parents[3] / ".env")

from app.db.session import get_db_operativa
from app.main import app
from app.models.minimal_models import Agenda, BaseOperativa
from app.services.appointments_service import get_appointments_statistic


engine_operativa = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionOperativa = sessionmaker(bind=engine_operativa)

app.dependency_overrides[get_db_operativa] = lambda: TestingSessionOperativa()

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_dbs():
    BaseOperativa.metadata.create_all(bind=engine_operativa)

    db_o = TestingSessionOperativa()
    try:
        db_o.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS citas (
                    id_cita INTEGER PRIMARY KEY,
                    id_paciente INTEGER NOT NULL,
                    id_agenda INTEGER NOT NULL,
                    asistio BOOLEAN
                )
                """
            )
        )

        db_o.add_all(
            [
                Agenda(
                    id_agenda=1,
                    id_doctor=80112457,
                    id_especialidad=2,
                    fecha=date(2026, 3, 31),
                    hora_inicio=time(8, 0),
                    hora_fin=time(8, 30),
                    estado=1,
                ),
                Agenda(
                    id_agenda=2,
                    id_doctor=80112457,
                    id_especialidad=2,
                    fecha=date(2026, 3, 31),
                    hora_inicio=time(9, 0),
                    hora_fin=time(9, 30),
                    estado=1,
                ),
                Agenda(
                    id_agenda=3,
                    id_doctor=80112457,
                    id_especialidad=2,
                    fecha=date(2026, 4, 2),
                    hora_inicio=time(10, 0),
                    hora_fin=time(10, 30),
                    estado=1,
                ),
            ]
        )
        db_o.commit()

        db_o.execute(
            text(
                """
                INSERT INTO citas (id_cita, id_paciente, id_agenda, asistio)
                VALUES (1, 1018442903, 1, NULL),
                       (2, 1018442903, 2, NULL),
                       (3, 1018442903, 3, NULL)
                """
            )
        )
        db_o.commit()
    finally:
        db_o.close()

    yield db_o

    try:
        db_o.execute(text("DROP TABLE IF EXISTS citas"))
        db_o.commit()
    finally:
        db_o.close()

    BaseOperativa.metadata.drop_all(bind=engine_operativa)


def test_unit_appointments_statistic_returns_daily_counts_with_gaps(setup_dbs):
    result = get_appointments_statistic(
        setup_dbs,
        start_date=date(2026, 3, 31),
        end_date=date(2026, 4, 2),
    )

    assert result == [
        {"fecha": date(2026, 3, 31), "numero_citas": 2},
        {"fecha": date(2026, 4, 1), "numero_citas": 0},
        {"fecha": date(2026, 4, 2), "numero_citas": 1},
    ]


def test_unit_appointments_statistic_rejects_inverted_range():
    response = client.get(
        "/api/appointments/statistic?startDate=2026-04-02&endDate=2026-03-31"
    )

    assert response.status_code == 400