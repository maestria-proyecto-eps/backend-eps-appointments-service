# Database Setup — Supabase + SQLAlchemy

## 1. Dependencia adicional

Instala `psycopg2` en tu entorno virtual:

```bash
pip install psycopg2-binary
```

Luego actualiza tu `requirements.txt`:

```bash
pip freeze > requirements.txt
```

---

## 2. Variables de entorno — `.env.example`

Crea un archivo `.env` basado en este ejemplo (no subas el `.env` real al repositorio):

```env
# .env.example
user=postgres
password=tu_password_de_supabase
host=db.xxxxxxxxxxxxxxxx.supabase.co
port=5432
dbname=postgres
```

---

## 3. Recomendación — `pydantic-settings` en `core/config.py`

Si el proyecto ya usa `pydantic-settings`, lo ideal es centralizar las variables ahí en lugar de leerlas directamente con `os.getenv`. Ejemplo mínimo:

```python
# core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    user: str
    password: str
    host: str
    port: int = 5432
    dbname: str

    class Config:
        env_file = ".env"

settings = Settings()
```

Luego en `database.py` importas `settings` y usas `settings.user`, `settings.host`, etc. Esto valida que todas las variables existan al iniciar la app, evitando errores silenciosos en runtime.

---

## 4. `database.py` — Código final

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv
import os

load_dotenv()

USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"

engine = create_engine(DATABASE_URL, poolclass=NullPool)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## 5. Por qué `sslmode=require` y `NullPool`

**`sslmode=require`**
Supabase vive en la nube y exige que la conexión vaya cifrada. Sin este parámetro, el servidor Supabase rechaza la conexión. Es básicamente el "https" de las conexiones a base de datos.

**`NullPool`**
SQLAlchemy por defecto mantiene un grupo de conexiones abiertas para reutilizarlas (pool). Supabase usa un intermediario llamado PgBouncer que administra las conexiones por su cuenta y tiene un límite bajo (especialmente en el plan gratuito). Si SQLAlchemy también guarda conexiones abiertas, los dos chocan y se agotan los slots disponibles. Con `NullPool`, SQLAlchemy abre y cierra cada conexión al momento de usarla, dejando que Supabase gestione todo sin conflictos.
