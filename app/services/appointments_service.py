from datetime import date

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
        raise HTTPException(status_code=404, detail="Appointment not found")
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
    today = date.today()
    if fecha <= today:
        raise HTTPException(
            status_code=400,
            detail="fecha must be greater than current server date",
        )

    with db.begin():
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
                "hora_inicio": hora_inicio,
            },
        ).mappings().first()

        if not agenda_row:
            raise HTTPException(status_code=404, detail="Slot not found in agenda")

        if agenda_row["estado"] not in AVAILABLE_AGENDA_STATES:
            raise HTTPException(status_code=409, detail="Slot is not available")

        future_active_count = db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM public.citas c
                JOIN public.agenda a ON a.id_agenda = c.id_agenda
                WHERE c.id_paciente = :id_paciente
                  AND a.fecha > :today
                """
            ),
            {"id_paciente": id_paciente, "today": today},
        ).scalar_one()

        if future_active_count >= 3:
            raise HTTPException(
                status_code=400,
                detail="Patient already has 3 future active appointments",
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
                    detail="Valid referral is required for this specialty",
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
