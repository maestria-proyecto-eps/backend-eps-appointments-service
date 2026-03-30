from datetime import date
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.minimal_models import Especialidad, Remision, Doctor, Usuario, Agenda
from app.schemas.availability import DoctorAvailabilityOut

def get_availability_slots(
        db_admin: Session,
        db_operativa: Session,
        id_paciente: int,
        specialty_id: int,
        start_date: date,
        end_date: date,
        doctor_id: int | None = None
) -> list[dict]:
    """
    Evalua reglas de negocio en la DB Administrativa y retorna
    los slots disponibles consultados en la DB Operativa.
    """

    # 1. Validacion de la especialidad (Admin DB)
    especialidad = db_admin.query(Especialidad).filter(
        Especialidad.id_especialidad == specialty_id
    ).first()

    if not especialidad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La especialidad proporcionada no existe."
        )

    # 2. Validacion de remision vigente (Admin DB)
    if especialidad.requiere_remision:
        remision_valida = db_admin.query(Remision).filter(
            Remision.id_paciente == id_paciente,
            Remision.id_especialidad == specialty_id,
            Remision.expiracion > date.today()
        ).first()

        if not remision_valida:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El paciente requiere una remision vigente para esta especialidad."
            )

    # 3. Obtencion de medicos activos (Admin DB)
    query_doctores = db_admin.query(Doctor).join(
        Usuario, Doctor.id_usuario == Usuario.id_usuario
    ).filter(
        Doctor.id_especialidad == specialty_id,
        Usuario.estado == True
    )

    if doctor_id:
        query_doctores = query_doctores.filter(Doctor.id_medico == doctor_id)

    doctores_activos = query_doctores.all()

    if not doctores_activos:
        return []

    # Se crea un diccionario para acceso rapido a los datos del doctor
    dict_doctores = {
        doc.id_medico: f"{doc.nombre} {doc.apellido}" for doc in doctores_activos
    }
    lista_ids_doctores = list(dict_doctores.keys())

    # 4. Obtencion de slots disponibles (Operativa DB)
    agendas_disponibles = db_operativa.query(Agenda).filter(
        Agenda.id_especialidad == specialty_id,
        Agenda.id_doctor.in_(lista_ids_doctores),
        Agenda.fecha >= start_date,
        Agenda.fecha <= end_date,
        Agenda.estado == 1
    ).order_by(Agenda.fecha.asc(), Agenda.hora_inicio.asc()).all()

    # 5. Agrupacion de resultados
    resultado_agrupado = {}
    for agenda in agendas_disponibles:
        doc_id = agenda.id_doctor
        if doc_id not in resultado_agrupado:
            resultado_agrupado[doc_id] = {
                "id_doctor": doc_id,
                "nombre_completo": dict_doctores[doc_id],
                "slots": []
            }

        resultado_agrupado[doc_id]["slots"].append({
            "id_agenda": agenda.id_agenda,
            "fecha": agenda.fecha,
            "hora_inicio": agenda.hora_inicio,
            "hora_fin": agenda.hora_fin
        })

    return list(resultado_agrupado.values())