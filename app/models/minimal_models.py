from sqlalchemy import Column, Integer, String, Boolean, Date, Time, ForeignKey
from app.db.session import BaseAdmin, BaseOperativa

# --- Modelos Base Administrativa ---

class Especialidad(BaseAdmin):
    __tablename__ = "especialidades"
    id_especialidad = Column(Integer, primary_key=True, index=True)
    nombre_especialidad = Column(String)
    requiere_remision = Column(Boolean)

class Usuario(BaseAdmin):
    __tablename__ = "usuarios"
    id_usuario = Column(Integer, primary_key=True, index=True)
    estado = Column(Boolean)

class Doctor(BaseAdmin):
    __tablename__ = "medicos"
    id_medico = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"))
    id_especialidad = Column(Integer, ForeignKey("especialidades.id_especialidad"))
    nombre = Column(String)
    apellido = Column(String)

# --- Modelos Base Operativa ---

class Agenda(BaseOperativa):
    __tablename__ = "agenda"
    id_agenda = Column(Integer, primary_key=True, index=True)
    id_doctor = Column(Integer, index=True)
    id_especialidad = Column(Integer)
    fecha = Column(Date, index=True)
    hora_inicio = Column(Time)
    hora_fin = Column(Time)
    estado = Column(Integer)

class Remision(BaseOperativa):
    __tablename__ = "remisiones"
    id_remision = Column(Integer, primary_key=True, index=True)
    id_paciente = Column(Integer, index=True)
    id_especialidad = Column(Integer)
    expiracion = Column(Date)