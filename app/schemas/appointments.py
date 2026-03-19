from datetime import date, time

from pydantic import BaseModel, ConfigDict


class AppointmentCreateRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id_especialidad": 1,
                "id_doctor": 71332991,
                "fecha": "2026-03-23",
                "hora_inicio": "08:00:00",
            }
        }
    )

    id_especialidad: int
    id_doctor: int
    fecha: date
    hora_inicio: time


class AppointmentOut(BaseModel):
    id_cita: int
    id_paciente: int
    id_agenda: int
    id_doctor: int
    id_especialidad: int
    fecha: date
    hora_inicio: time
    hora_fin: time
    estado_agenda: int | None
    id_remision: int | None
    asistio: bool | None


class MyAppointmentsResponse(BaseModel):
    future: list[AppointmentOut]
    past: list[AppointmentOut]
