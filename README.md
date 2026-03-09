# 🏥 Backend EPS - FastAPI

Backend desarrollado con **FastAPI** para la gestión de servicios relacionados con una EPS (Entidad Promotora de Salud).
Este proyecto sigue una estructura modular y escalable, preparada para entornos de desarrollo y producción.

---

# 🚀 Tecnologías Principales

* FastAPI
* Uvicorn
* SQLAlchemy
* Pydantic Settings
* Python-JOSE (JWT)
* Python-dotenv

---

# ⚙️ Configuración del Entorno

## 1️⃣ Crear entorno virtual (venv)

### 🐧 Linux / Mac

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 🪟 Windows (PowerShell)

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

Si da error de políticas:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### 🪟 Windows (CMD)

```cmd
python -m venv venv
venv\Scripts\activate.bat
```

---

## 2️⃣ Instalar dependencias

Con el entorno virtual activado:

### 🐧 Linux / Mac

```bash
pip install -r requirements.txt
```

### 🪟 Windows

```bash
pip install -r requirements.txt
```

> ✅ El comando es el mismo en ambos sistemas si el entorno está activado correctamente.

### instalar otras dependencias
```bash
pip install nombre_dependencia
```

### guardar cambios de dependencias en requirements.txt
```bash
pip freeze > requirements.txt
```

---

# ▶️ Ejecutar el Backend

Desde la raíz del proyecto:

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Acceder a:

* 📄 Documentación Swagger:
  http://127.0.0.1:8000/docs

* 📘 Documentación Redoc:
  http://127.0.0.1:8000/redoc

---

# 📦 Dependencias Principales

## 🔹 FastAPI

Framework web moderno y rápido para construir APIs con Python.

## 🔹 Uvicorn

Servidor ASGI que ejecuta la aplicación FastAPI.

## 🔹 python-dotenv

Permite cargar variables de entorno desde un archivo `.env`.

## 🔹 pydantic-settings

Gestión estructurada y tipada de configuraciones usando Pydantic.

## 🔹 python-jose

Implementación de JWT para autenticación y autorización.

## 🔹 SQLAlchemy

ORM que permite interactuar con bases de datos relacionales usando modelos en Python.

---

# 🔐 Variables de Entorno

El proyecto utiliza variables de entorno para configuración sensible.

Debes:

1. Crear un archivo `.env` en la raíz del proyecto.
2. Copiar el contenido de `.env.example`.
3. Ajustar los valores según tu entorno.

### 📌 Convención estándar

```
.env.example
```

Este archivo contiene las variables necesarias **sin datos sensibles**, por ejemplo:

```env
# DB
DB_URL=postgresql://user:password@localhost/db

# jwt
JWT_SECRET=your_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRES_MINUTES=30
```

Luego creas tu archivo real:

```
.env
```

⚠️ El archivo `.env` no debe subirse al repositorio (agregarlo al `.gitignore`).
