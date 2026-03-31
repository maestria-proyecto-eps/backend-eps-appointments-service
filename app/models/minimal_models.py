from sqlalchemy import Column, Integer, String, Boolean, Date, Time, ForeignKey, BigInteger, TIMESTAMP, SmallInteger
from sqlalchemy.orm import relationship
from app.db.session import BaseAdmin, BaseOperativa

# --- Modelos Base Administrativa ---

class Especialidad(BaseAdmin):
    __tablename__ = "especialidades"
    id_especialidad = Column(Integer, primary_key=True, index=True)
    nombre_especialidad = Column(String(50), nullable=False)
    requiere_remision = Column(Boolean, default=False)

    medicos = relationship("Doctor", back_populates="specialty")

    remisiones = relationship(
        "Especialidad",
        secondary="especialidades_remiten",
        primaryjoin="Especialidad.id_especialidad == SpecialtyRemission.id_especialidad_que_remite",
        secondaryjoin="Especialidad.id_especialidad == SpecialtyRemission.id_especialidad_remitida",
        backref="remitido_por"
    )

class SpecialtyRemission(BaseAdmin):
    __tablename__ = "especialidades_remiten"
    id_especialidad_remitida = Column(Integer, ForeignKey("especialidades.id_especialidad"), primary_key=True)
    id_especialidad_que_remite = Column(Integer, ForeignKey("especialidades.id_especialidad"), primary_key=True)

class Usuario(BaseAdmin):
    __tablename__ = "usuarios"
    id_usuario = Column(Integer, primary_key=True)
    num_documento = Column(BigInteger, ForeignKey("persona.num_documento"), nullable=True)
    password = Column(String(60), nullable=False)

    id_rol = Column(Integer, ForeignKey("roles.id_rol"), nullable=False)
    estado = Column(Boolean, nullable=False)
    intentos_login = Column(SmallInteger, nullable=False, default=0)
    tiempo_de_fallo_login = Column(TIMESTAMP, nullable=True)

    rol = relationship("Role", back_populates="usuarios")
    persona = relationship("Persona", back_populates="usuario")

class Persona(BaseAdmin):
    __tablename__ = "persona"
    num_documento = Column(BigInteger, primary_key=True)
    nombres = Column(String(50), nullable=False)
    apellidos = Column(String(50), nullable=False)

    usuario = relationship("Usuario", back_populates="persona", uselist=False)

class Doctor(BaseAdmin):
    __tablename__ = "medicos"
    id_medico = Column(BigInteger, ForeignKey("persona.num_documento"), primary_key=True)
    num_licencia = Column(Integer, unique=True, nullable=False)
    id_especialidad = Column(Integer, ForeignKey("especialidades.id_especialidad"), nullable=False)


    specialty = relationship("Especialidad", back_populates="medicos")
    persona = relationship("Persona", lazy="joined")

class Role(BaseAdmin):
    __tablename__ = "roles"
    id_rol= Column(Integer, primary_key=True)
    nombre_rol= Column(String(50), nullable=False)

    usuarios = relationship("Usuario", back_populates="rol")

# --- Modelos Base Operativa ---

class Agenda(BaseOperativa):
    __tablename__ = "agenda"
    id_agenda = Column(Integer, primary_key=True, index=True)

    id_doctor = Column(BigInteger, index=True)
    id_especialidad = Column(Integer)
    fecha = Column(Date, index=True)
    hora_inicio = Column(Time)
    hora_fin = Column(Time)
    estado = Column(Integer)

class Remision(BaseOperativa):
    __tablename__ = "remisiones"

    id_remision = Column(Integer, primary_key=True, index=True)
    id_paciente = Column(BigInteger, index=True)
    id_especialidad = Column(Integer)
    expiracion = Column(Date)
    id_registro = Column(Integer, nullable=False)