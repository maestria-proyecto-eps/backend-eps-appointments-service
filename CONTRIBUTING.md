
# 📁 Estructura del Proyecto

```text
app/
├── main.py
├── routers/
├── models/
├── schemas/
├── services/
├── core/
```

---

## 📌 `/routers`

Contiene los endpoints (rutas HTTP).
Aquí se definen los controladores que reciben y responden peticiones.

Ejemplo:

* usuarios.py
* auth.py

---

## 📌 `/models`

Modelos ORM de SQLAlchemy.
Representan las tablas en la base de datos.

Ejemplo:

```python
class User(Base):
    __tablename__ = "users"
```

---

## 📌 `/schemas`

Modelos Pydantic para validación y serialización de datos.
Se usan para entrada (request) y salida (response).

Ejemplo:

```python
class UserCreate(BaseModel):
```

---

## 📌 `/services`

Contiene la lógica de negocio.
Aquí se implementan las reglas del sistema y operaciones sobre los modelos.

---

## 📌 `/core`

Configuraciones globales del proyecto.

Ejemplos:

* config.py → Manejo de variables de entorno
* security.py → JWT, hashing
* settings.py → Configuración general

---



# 🌳 Convención de Ramas (GitFlow Simplificado)

Este proyecto utiliza un **GitFlow simplificado** con rama de QA como compuerta de calidad antes de producción.

### 📌 Estructura de ramas

```
main         ← producción
qa           ← quality gate (validación antes de prod)
develop      ← integración / entorno dev
feature/*
bugfix/*
hotfix/*
```

---

## 🔹 `main`

* Contiene únicamente código estable y listo para producción.
* Al hacer merge aquí se **despliega automáticamente a producción** (Render).
* No se permite hacer push directo.
* Solo recibe PRs desde:
  * `qa` (nuevas versiones validadas)
  * `hotfix/*` (correcciones críticas)

---

## 🔹 `qa`

* Rama de **quality gate** — validación final antes de producción.
* **No tiene entorno de despliegue propio**, solo ejecuta CI (lint + tests).
* Recibe PRs desde `develop`.
* Desde aquí se abre PR hacia `main` para ir a producción.

---

## 🔹 `develop`

* Rama de integración y desarrollo.
* Al hacer merge aquí se **despliega automáticamente al entorno de desarrollo** (Render).
* Recibe merges desde:
  * `feature/*`
  * `bugfix/*`
  * `hotfix/*` (después de aplicar en `main`)

---

## 🚀 `feature/*`

Ramas para nuevas funcionalidades.

### 📌 Convención de nombres

```
feature/<descripcion-corta>
```

### ✅ Ejemplos

```
feature/login-jwt
feature/roi-editor
feature/notifications-module
```

### 🔄 Flujo

1. Se crea desde `develop`
2. Se implementa la funcionalidad
3. Se abre Pull Request hacia `develop`
4. CI valida automáticamente (lint + tests)
5. Se elimina después del merge

---

## 🐛 `bugfix/*`

Ramas para corregir errores detectados en `develop` o `qa` antes de pasar a producción.

### 📌 Convención de nombres

```
bugfix/<descripcion-corta>
```

### ✅ Ejemplos

```
bugfix/fix-token-refresh
bugfix/null-camera-error
```

### 🔄 Flujo

1. Se crea desde `develop`
2. Se corrige el error
3. Se hace Pull Request hacia `develop`
4. Se elimina después del merge

> ⚠ Si el error está en producción, debe usarse `hotfix/*`, no `bugfix/*`.

---

## 🚑 `hotfix/*`

Ramas para correcciones críticas en producción.

### 📌 Convención de nombres

```
hotfix/<descripcion-corta>
```

### ✅ Ejemplos

```
hotfix/security-patch
hotfix/crash-on-startup
```

### 🔄 Flujo

1. Se crea desde `main`
2. Se corrige el problema
3. Se hace PR hacia:
   * `main` (se despliega a producción automáticamente)
   * `develop` (obligatorio para evitar regresiones)
4. Se elimina después del merge

---

## 📌 Reglas Generales

* ❌ No hacer push directo a `main`, `qa` ni `develop`
* ✅ Todo cambio debe pasar por Pull Request
* ✅ Los PRs ejecutan CI automáticamente (lint + tests)
* ✅ Mantener nombres descriptivos y en kebab-case
* ✅ Eliminar ramas después del merge
* ✅ Mantener commits claros y atómicos

---

## 🔁 Flujo General

```
feature/* ──PR──→ develop ──PR──→ qa ──PR──→ main
bugfix/*  ──PR──→ develop ──PR──→ qa ──PR──→ main
hotfix/*  ──PR──→ main + develop
```

---

## 🚀 CI/CD y Entornos

### Integración Continua (CI) — `ci.yml`

Se ejecuta automáticamente al abrir un **Pull Request** hacia `develop`, `qa` o `main`:

* **Lint** — flake8 (errores de sintaxis Python)
* **Tests** — pytest (si existen tests en el repo)

> El PR no debe mergearse si CI falla.

### Despliegue Continuo (CD) — Render Auto-Deploy (Docker)

El servicio está **dockerizado**. Render detecta automáticamente el `Dockerfile` y construye la imagen del contenedor.

Render está configurado con **"Auto-Deploy: After CI Checks Pass"**, lo que significa que el despliegue se dispara automáticamente cuando:

1. Un PR se mergea a la rama configurada en Render
2. Los checks de CI en GitHub pasan exitosamente
3. Render construye la imagen Docker y despliega el contenedor

| Rama | Entorno | Servicio Render |
|---|---|---|
| `develop` | Development | Servicio apuntando a rama `develop` |
| `main` | Production | Servicio apuntando a rama `main` |

> `qa` no tiene despliegue — funciona como compuerta de calidad (solo CI).
>
> **No se necesita workflow de CD** (`cd.yml`) para los backends — Render maneja el deploy de forma nativa.

### 🐳 Docker

El proyecto incluye un `Dockerfile` optimizado para producción:

* **Base**: `python:3.12-slim` (imagen ligera)
* **Layer caching**: Las dependencias se instalan antes de copiar el código (builds más rápidos)
* **Puerto**: Se usa la variable `$PORT` inyectada por Render (default: 10000)
* **`.dockerignore`**: Excluye archivos innecesarios (tests, .git, .env, etc.)

Para correr localmente con Docker:

```bash
docker build -t backend-eps-appointments-service .
docker run -p 8000:8000 -e PORT=8000 backend-eps-appointments-service
```
