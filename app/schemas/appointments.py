from datetime import date, time

from pydantic import BaseModel


class AppointmentCreateRequest(BaseModel):
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
