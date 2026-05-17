from datetime import date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

AVAILABLE_AGENDA_STATES = {1}
BLOCKED_AGENDA_STATE = 0


def _row_to_appointment(row) -> dict:
    return {
        "id_cita": row.id_cita,
        "id_paciente": row.id_paciente,
        "id_agenda": row.id_agenda,
        "id_doctor": row.id_doctor,
        "id_especialidad": row.id_especialidad,
        "fecha": row.fecha,
        "hora_inicio": row.hora_inicio,
        "hora_fin": row.hora_fin,
        "estado_agenda": row.estado_agenda,
        "id_remision": row.id_remision,
        "asistio": row.asistio,
    }


def _requires_referral(db: Session, id_especialidad: int) -> bool:
    has_lower = db.execute(
        text("SELECT to_regclass('public.especialidades') IS NOT NULL")
    ).scalar_one()

    if has_lower:
        value = db.execute(
            text(
                "SELECT requiere_remision FROM public.especialidades "
                "WHERE id_especialidad = :id_especialidad"
            ),
            {"id_especialidad": id_especialidad},
        ).scalar_one_or_none()
        return bool(value)

    has_upper = db.execute(
        text('SELECT to_regclass(\'public."ESPECIALIDADES"\') IS NOT NULL')
    ).scalar_one()

    if has_upper:
        value = db.execute(
            text(
                'SELECT "requiere_remision" FROM public."ESPECIALIDADES" '
                'WHERE "id_especialidad" = :id_especialidad'
            ),
            {"id_especialidad": id_especialidad},
        ).scalar_one_or_none()
        return bool(value)

    return False


def _fetch_appointment_by_id(db: Session, id_cita: int) -> dict:
    row = db.execute(
        text(
            """
            SELECT
                c.id_cita,
                c.id_paciente,
                c.id_agenda,
                a.id_doctor,
                a.id_especialidad,
                a.fecha,
                a.hora_inicio,
                a.hora_fin,
                a.estado AS estado_agenda,
                c.id_remision,
                c.asistio
            FROM public.citas c
            JOIN public.agenda a ON a.id_agenda = c.id_agenda
            WHERE c.id_cita = :id_cita
            """
        ),
        {"id_cita": id_cita},
    ).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return _row_to_appointment(row)


def create_appointment(
    db: Session,
    *,
    id_paciente: int,
    id_especialidad: int,
    id_doctor: int,
    fecha,
    hora_inicio,
) -> dict:
    # Normalize client-provided time to server-local naive time for consistent comparisons and SQL filtering.
    slot_time = hora_inicio.replace(tzinfo=None) if getattr(hora_inicio, "tzinfo", None) else hora_inicio

    now = datetime.now()
    selected_slot = datetime.combine(fecha, slot_time)
    today = now.date()

    if selected_slot <= now:
        raise HTTPException(
            status_code=400,
            detail="La cita seleccionada debe ser posterior a la hora actual del servidor",
        )

    with db.begin_nested():
        agenda_row = db.execute(
            text(
                """
                SELECT id_agenda, estado
                FROM public.agenda
                WHERE id_doctor = :id_doctor
                  AND id_especialidad = :id_especialidad
                  AND fecha = :fecha
                  AND hora_inicio = :hora_inicio
                FOR UPDATE
                """
            ),
            {
                "id_doctor": id_doctor,
                "id_especialidad": id_especialidad,
                "fecha": fecha,
                "hora_inicio": slot_time,
            },
        ).mappings().first()

        if not agenda_row:
            raise HTTPException(status_code=404, detail="Horario no encontrado en la agenda")

        if agenda_row["estado"] not in AVAILABLE_AGENDA_STATES:
            raise HTTPException(status_code=409, detail="El horario no esta disponible")

        future_active_count = db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM public.citas c
                JOIN public.agenda a ON a.id_agenda = c.id_agenda
                WHERE c.id_paciente = :id_paciente
                  AND (
                      a.fecha > :today
                      OR (a.fecha = :today AND a.hora_inicio > :current_time)
                  )
                """
            ),
            {
                "id_paciente": id_paciente,
                "today": today,
                "current_time": now.time(),
            },
        ).scalar_one()

        if future_active_count >= 3:
            raise HTTPException(
                status_code=400,
                detail="El paciente ya tiene 3 citas futuras activas",
            )

        if _requires_referral(db, id_especialidad):
            has_valid_referral = db.execute(
                text(
                    """
                    SELECT 1
                    FROM public.remisiones r
                    WHERE r.id_paciente = :id_paciente
                      AND r.id_especialidad = :id_especialidad
                      AND r.expiracion > :today
                    LIMIT 1
                    """
                ),
                {
                    "id_paciente": id_paciente,
                    "id_especialidad": id_especialidad,
                    "today": today,
                },
            ).first()

            if not has_valid_referral:
                raise HTTPException(
                    status_code=400,
                    detail="Se requiere una remision valida para esta especialidad",
                )

        id_cita = None
        try:
            id_cita = db.execute(
                text(
                    """
                    INSERT INTO public.citas (id_paciente, id_agenda, asistio)
                    VALUES (:id_paciente, :id_agenda, NULL)
                    RETURNING id_cita
                    """
                ),
                {"id_paciente": id_paciente, "id_agenda": agenda_row["id_agenda"]},
            ).scalar_one()
        except IntegrityError:
            next_id = db.execute(
                text("SELECT COALESCE(MAX(id_cita), 0) + 1 FROM public.citas")
            ).scalar_one()
            id_cita = db.execute(
                text(
                    """
                    INSERT INTO public.citas (id_cita, id_paciente, id_agenda, asistio)
                    VALUES (:id_cita, :id_paciente, :id_agenda, NULL)
                    RETURNING id_cita
                    """
                ),
                {
                    "id_cita": next_id,
                    "id_paciente": id_paciente,
                    "id_agenda": agenda_row["id_agenda"],
                },
            ).scalar_one()

        db.execute(
            text(
                """
                UPDATE public.agenda
                SET estado = :blocked_state
                WHERE id_agenda = :id_agenda
                """
            ),
            {
                "blocked_state": BLOCKED_AGENDA_STATE,
                "id_agenda": agenda_row["id_agenda"],
            },
        )
    db.commit()
    return _fetch_appointment_by_id(db, id_cita)


def list_appointments(
    db: Session,
    *,
    fecha=None,
    estado=None,
    id_especialidad=None,
    id_doctor=None,
) -> list[dict]:
    rows = db.execute(
        text(
            """
            SELECT
                c.id_cita,
                c.id_paciente,
                c.id_agenda,
                a.id_doctor,
                a.id_especialidad,
                a.fecha,
                a.hora_inicio,
                a.hora_fin,
                a.estado AS estado_agenda,
                c.id_remision,
                c.asistio
            FROM public.citas c
            JOIN public.agenda a ON a.id_agenda = c.id_agenda
            WHERE (:fecha IS NULL OR a.fecha = :fecha)
              AND (:estado IS NULL OR a.estado = :estado)
              AND (:id_especialidad IS NULL OR a.id_especialidad = :id_especialidad)
              AND (:id_doctor IS NULL OR a.id_doctor = :id_doctor)
            ORDER BY a.fecha, a.hora_inicio
            """
        ),
        {
            "fecha": fecha,
            "estado": estado,
            "id_especialidad": id_especialidad,
            "id_doctor": id_doctor,
        },
    ).mappings().all()

    return [_row_to_appointment(r) for r in rows]


def list_my_appointments(db: Session, *, id_paciente: int) -> dict:
    today = date.today()

    rows = db.execute(
        text(
            """
            SELECT
                c.id_cita,
                c.id_paciente,
                c.id_agenda,
                a.id_doctor,
                a.id_especialidad,
                a.fecha,
                a.hora_inicio,
                a.hora_fin,
                a.estado AS estado_agenda,
                c.id_remision,
                c.asistio
            FROM public.citas c
            JOIN public.agenda a ON a.id_agenda = c.id_agenda
            WHERE c.id_paciente = :id_paciente
            ORDER BY a.fecha DESC, a.hora_inicio DESC
            """
        ),
        {"id_paciente": id_paciente},
    ).mappings().all()

    future = []
    past = []
    for row in rows:
        item = _row_to_appointment(row)
        if row["fecha"] >= today:
            future.append(item)
        else:
            past.append(item)

    return {"future": future, "past": past}


def cancel_appointment(
    db: Session,
    *,
    id_cita: int,
    id_paciente: int,
    razon: str,
) -> dict:
    _ = razon

    with db.begin_nested():
        appointment_row = db.execute(
            text(
                """
                SELECT
                    c.id_cita,
                    c.id_paciente,
                    c.id_agenda,
                    a.fecha,
                    a.hora_inicio
                FROM public.citas c
                JOIN public.agenda a ON a.id_agenda = c.id_agenda
                WHERE c.id_cita = :id_cita
                FOR UPDATE
                """
            ),
            {"id_cita": id_cita},
        ).mappings().first()

        if not appointment_row:
            raise HTTPException(status_code=404, detail="Cita no encontrada")

        if appointment_row["id_paciente"] != id_paciente:
            raise HTTPException(status_code=403, detail="No autorizado para cancelar esta cita")

        appointment_datetime = datetime.combine(
            appointment_row["fecha"],
            appointment_row["hora_inicio"],
        )
        if appointment_datetime <= datetime.now():
            raise HTTPException(
                status_code=422,
                detail="Solo se pueden cancelar citas futuras",
            )

        db.execute(
            text(
                """
                UPDATE public.agenda
                SET estado = :available_state
                WHERE id_agenda = :id_agenda
                """
            ),
            {
                "available_state": 1,
                "id_agenda": appointment_row["id_agenda"],
            },
        )

        db.execute(
            text(
                """
                DELETE FROM public.citas
                WHERE id_cita = :id_cita
                """
            ),
            {"id_cita": id_cita},
        )
    db.commit()  
    return {"message": "Cita cancelada exitosamente"}


def get_appointments_statistic(
    db: Session,
    *,
    start_date: date,
    end_date: date,
) -> list[dict]:
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="La fecha inicial no puede ser mayor que la fecha final",
        )

    rows = db.execute(
        text(
            """
            SELECT
                a.fecha AS fecha,
                COUNT(c.id_cita) AS numero_citas
            FROM citas c
            JOIN agenda a ON a.id_agenda = c.id_agenda
            WHERE a.fecha BETWEEN :start_date AND :end_date
            GROUP BY a.fecha
            ORDER BY a.fecha
            """
        ),
        {
            "start_date": start_date,
            "end_date": end_date,
        },
    ).mappings().all()

    counts_by_date = {}
    for row in rows:
        row_date = row["fecha"]
        if isinstance(row_date, str):
            row_date = date.fromisoformat(row_date)
        counts_by_date[row_date] = int(row["numero_citas"])

    result = []
    current_date = start_date
    while current_date <= end_date:
        result.append(
            {
                "fecha": current_date,
                "numero_citas": counts_by_date.get(current_date, 0),
            }
        )
        current_date += timedelta(days=1)

    return result
