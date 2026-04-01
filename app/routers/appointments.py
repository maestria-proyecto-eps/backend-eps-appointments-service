from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.appointments import (
    AppointmentCancelRequest,
    AppointmentCancelResponse,
    AppointmentCreateRequest,
    AppointmentOut,
    MyAppointmentsResponse,
)
from app.services.appointments_service import (
    cancel_appointment,
    create_appointment,
    list_appointments,
    list_my_appointments,
)

router = APIRouter(prefix="/api", tags=["appointments"])


def get_authenticated_patient_id(
    x_patient_id: Annotated[
        int | None,
        Header(
            alias="X-Patient-Id",
            description="Identificador del paciente autenticado.",
            examples=[1],
        ),
    ] = None,
) -> int:
    if x_patient_id is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=401,
            detail="Falta el identificador del paciente autenticado en el encabezado X-Patient-Id",
        )
    return x_patient_id


@router.post(
    "/appointments",
    response_model=AppointmentOut,
    summary="Crear cita",
    description=(
        "Crea una cita para el paciente autenticado. "
        "Valida disponibilidad del slot en agenda, remisión cuando aplica, "
        "máximo de 3 citas futuras activas y que la fecha/hora seleccionada sea posterior a la hora actual."
    ),
    responses={
        400: {"description": "Error de validación de negocio"},
        401: {"description": "Paciente no autenticado"},
        404: {"description": "Horario no encontrado"},
        409: {"description": "Horario no disponible"},
    },
)
def create_appointment_endpoint(
    payload: AppointmentCreateRequest,
    db: Session = Depends(get_db),
    id_paciente: int = Depends(get_authenticated_patient_id),
) -> dict:
    return create_appointment(
        db,
        id_paciente=id_paciente,
        id_especialidad=payload.id_especialidad,
        id_doctor=payload.id_doctor,
        fecha=payload.fecha,
        hora_inicio=payload.hora_inicio,
    )


@router.get(
    "/appointments",
    response_model=list[AppointmentOut],
    summary="Listar citas",
    description="Lista citas con filtros opcionales por fecha, estado, especialidad y doctor.",
)
def list_appointments_endpoint(
    fecha: date | None = Query(default=None, description="Filtra por agenda.fecha (YYYY-MM-DD)."),
    estado: int | None = Query(default=None, description="Filtra por agenda.estado."),
    id_especialidad: int | None = Query(default=None, description="Filtra por agenda.id_especialidad."),
    id_doctor: int | None = Query(default=None, description="Filtra por agenda.id_doctor."),
    db: Session = Depends(get_db),
) -> list[dict]:
    return list_appointments(
        db,
        fecha=fecha,
        estado=estado,
        id_especialidad=id_especialidad,
        id_doctor=id_doctor,
    )


@router.get(
    "/patients/me/appointments",
    response_model=MyAppointmentsResponse,
    summary="Mis citas",
    description=(
        "Retorna las citas del paciente autenticado separadas en "
        "future (agenda.fecha >= fecha actual) y past (agenda.fecha < fecha actual)."
    ),
    responses={401: {"description": "Paciente no autenticado"}},
)
def list_my_appointments_endpoint(
    db: Session = Depends(get_db),
    id_paciente: int = Depends(get_authenticated_patient_id),
) -> dict:
    return list_my_appointments(db, id_paciente=id_paciente)


@router.put(
    "/appointments/{id}/cancel",
    response_model=AppointmentCancelResponse,
    summary="Cancelar cita",
    description="Permite al paciente autenticado cancelar una cita futura de su propiedad.",
    responses={
        401: {"description": "Paciente no autenticado"},
        403: {"description": "Cita no pertenece al paciente autenticado"},
        404: {"description": "Cita no encontrada"},
        422: {"description": "Solo se pueden cancelar citas futuras"},
    },
)
def cancel_appointment_endpoint(
    id: int,
    payload: AppointmentCancelRequest,
    db: Session = Depends(get_db),
    id_paciente: int = Depends(get_authenticated_patient_id),
) -> dict:
    return cancel_appointment(
        db,
        id_cita=id,
        id_paciente=id_paciente,
        razon=payload.razon,
    )
