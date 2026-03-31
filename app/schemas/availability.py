from pydantic import BaseModel
from datetime import date, time
from typing import List

class SlotOut(BaseModel):
    id_agenda: int
    fecha: date
    hora_inicio: time
    hora_fin: time

class DoctorAvailabilityOut(BaseModel):
    id_medico: int
    nombre_medico: str
    slots: List[SlotOut]