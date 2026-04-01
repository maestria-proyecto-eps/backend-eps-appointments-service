from datetime import date
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.minimal_models import Especialidad, Doctor, Persona, Agenda, Remision
from app.schemas.availability import DoctorAvailabilityOut, SlotOut

def get_availability_slots(
        db_admin: Session,
        db_operativa: Session,
        id_paciente: int,
        specialty_id: int,
        start_date: date,
        end_date: date,
        doctor_id: int | None = None
) -> list[DoctorAvailabilityOut]:

    # 1. Validar Especialidad en BD Admin
    especialidad = db_admin.query(Especialidad).filter(Especialidad.id_especialidad == specialty_id).first()
    if not especialidad:
        raise HTTPException(status_code=404, detail="Especialidad no encontrada")

    # 2. Validar Remisión en BD Operativa (si aplica)
    if especialidad.requiere_remision:
        remision_activa = db_operativa.query(Remision).filter(
            Remision.id_paciente == id_paciente,
            Remision.id_especialidad == specialty_id,
            Remision.expiracion >= date.today()
        ).first()

        if not remision_activa:
            raise HTTPException(
                status_code=403,
                detail="El paciente no cuenta con una remisión vigente para esta especialidad."
            )

    # 3. Buscar slots en BD Operativa
    query_agenda = db_operativa.query(Agenda).filter(
        Agenda.id_especialidad == specialty_id,
        Agenda.fecha >= start_date,
        Agenda.fecha <= end_date,
        Agenda.estado == 1 # Disponible
    )
    if doctor_id:
        query_agenda = query_agenda.filter(Agenda.id_doctor == doctor_id)

    agendas = query_agenda.all()

    if not agendas:
        return []

    # 4. Agrupar por doctor y cruzar con BD Admin para obtener nombres
    doctor_ids = list(set([a.id_doctor for a in agendas]))
    doctores_admin = db_admin.query(Doctor).join(Persona).filter(Doctor.id_medico.in_(doctor_ids)).all()

    map_doctores = {
        d.id_medico: f"{d.persona.nombres} {d.persona.apellidos}"
        for d in doctores_admin
    }

    # 5. Construir respuesta
    agrupado = {}
    for agenda in agendas:
        doc_id = agenda.id_doctor
        if doc_id not in agrupado:
            agrupado[doc_id] = {
                "id_medico": doc_id,
                "nombre_medico": map_doctores.get(doc_id, "Médico Desconocido"),
                "slots": []
            }
        agrupado[doc_id]["slots"].append(
            SlotOut(
                id_agenda=agenda.id_agenda,
                fecha=agenda.fecha,
                hora_inicio=agenda.hora_inicio,
                hora_fin=agenda.hora_fin
            )
        )

    return [DoctorAvailabilityOut(**data) for data in agrupado.values()]