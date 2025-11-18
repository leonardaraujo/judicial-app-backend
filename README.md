
# Correr el servidor en desarrollo (local)
uv run uvicorn main:app --reload --env-file .env.dev

# Correr en VPS (producción)
env $(cat .env.prod | xargs) gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000

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

# Modo .venv vps
source .venv/bin/activate


# Actualizacion de codigo en vps
git fetch origin
git checkout main
git reset --hard origin/main