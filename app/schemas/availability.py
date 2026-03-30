from pydantic import BaseModel
from datetime import date, time

class SlotOut(BaseModel):
    id_agenda: int
    fecha: date
    hora_inicio: time
    hora_fin: time

class DoctorAvailabilityOut(BaseModel):
    id_doctor: int
    nombres: str
    apellidos: str
    slots: list[SlotOut]