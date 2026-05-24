from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db_admin_audit, get_db_operativa_audit
from app.schemas.appointments import (
    AppointmentCancelRequest,
    AppointmentCancelResponse,
    AppointmentCreateRequest,
    AppointmentOut,
    AppointmentStatisticOut,
    MyAppointmentsResponse,
)

from app.schemas.availability import DoctorAvailabilityOut
from app.services.appointments_service import (
    cancel_appointment,
    create_appointment,
    get_appointments_statistic,
    list_appointments,
    list_my_appointments,
)
from app.services.availability_service import get_availability_slots
from app.core.dependencias import RequireRole

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

@router.get(
    "/appointments/availability",
    response_model=list[DoctorAvailabilityOut],
    summary="Consultar disponibilidad",
    responses={
        403: {"description": "Sin remision vigente"},
        404: {"description": "Especialidad no encontrada"},
    },
    dependencies=[Depends(RequireRole(["Paciente"]))]
)
def get_availability_endpoint(
        specialty_id: int = Query(..., description="ID especialidad"),
        startDate: date = Query(..., description="Fecha inicial (YYYY-MM-DD)"),
        endDate: date = Query(..., description="Fecha final (YYYY-MM-DD)"),
        doctor_id: int | None = Query(None, description="Filtro opcional por doctor"),
        db_admin: Session = Depends(get_db_admin_audit),
        db_operativa: Session = Depends(get_db_operativa_audit),
        id_paciente: int = Depends(get_authenticated_patient_id),
):
    return get_availability_slots(
        db_admin=db_admin,
        db_operativa=db_operativa,
        id_paciente=id_paciente,
        specialty_id=specialty_id,
        start_date=startDate,
        end_date=endDate,
        doctor_id=doctor_id
    )
    
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
    dependencies=[Depends(RequireRole(["Paciente"]))]
)
def create_appointment_endpoint(
    payload: AppointmentCreateRequest,
    db: Session = Depends(get_db_operativa_audit),
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
    dependencies=[Depends(RequireRole(["Paciente", "Médico"]))]
)
def list_appointments_endpoint(
    fecha: date | None = Query(default=None, description="Filtra por agenda.fecha (YYYY-MM-DD)."),
    estado: int | None = Query(default=None, description="Filtra por agenda.estado."),
    id_especialidad: int | None = Query(default=None, description="Filtra por agenda.id_especialidad."),
    id_doctor: int | None = Query(default=None, description="Filtra por agenda.id_doctor."),
    db: Session = Depends(get_db_operativa_audit),
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
    dependencies=[Depends(RequireRole(["Paciente"]))]
)
def list_my_appointments_endpoint(
    db: Session = Depends(get_db_operativa_audit),
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
    dependencies=[Depends(RequireRole(["Paciente"]))]
)
def cancel_appointment_endpoint(
    id: int,
    payload: AppointmentCancelRequest,
    db: Session = Depends(get_db_operativa_audit),
    id_paciente: int = Depends(get_authenticated_patient_id),
) -> dict:
    return cancel_appointment(
        db,
        id_cita=id,
        id_paciente=id_paciente,
        razon=payload.razon,
    )


@router.get(
    "/appointments/statistic",
    response_model=list[AppointmentStatisticOut],
    summary="Estadística de citas",
    description="Devuelve el número de citas por día dentro de un rango de fechas.",
    dependencies=[Depends(RequireRole(["Talento Humano"]))]
)
def get_appointments_statistic_endpoint(
    startDate: date = Query(..., description="Fecha inicial (YYYY-MM-DD)."),
    endDate: date = Query(..., description="Fecha final (YYYY-MM-DD)."),
    db_operativa: Session = Depends(get_db_operativa_audit),
) -> list[dict]:
    return get_appointments_statistic(
        db_operativa,
        start_date=startDate,
        end_date=endDate,
    )
