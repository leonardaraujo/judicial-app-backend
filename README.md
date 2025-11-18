
# Correr el servidor en desarrollo (local)
uv run uvicorn main:app --reload --env-file .env.dev

# Correr en VPS (producción)
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --env-file .env.prod

# Correr el servidor
uv run uvicorn main:app --reload

# Configuracion inicial de tablas
set DOTENV_FILE=.env.dev
uv run python -m database.initial.create_tables

# Configuración inicial de tablas (producción)
## Windows
set DOTENV_FILE=.env.prod
python -m database.initial.create_tables
## Linux
export DOTENV_FILE=.env.prod
python -m database.initial.create_tables

# Instalar dependencias
uv sync
