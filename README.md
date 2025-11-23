

# Guía rápida de uso

## 1. Instalar dependencias
```bash
uv sync
```

## 2. Activar entorno virtual (VPS/Linux)
```bash
source .venv/bin/activate
```

## 3. Configuración inicial de tablas

### Desarrollo
#### Windows
```powershell
uv run --env-file .env.dev python -m database.initial.create_tables
uv run python -m database.initial.init_qdrant
```
#### Linux/macOS
```bash
export DOTENV_FILE=.env.dev
python -m database.initial.create_tables
```

### Producción
#### Windows
```powershell
set DOTENV_FILE=.env.prod
python -m database.initial.create_tables
```
#### Linux/macOS
```bash
export DOTENV_FILE=.env.prod
python -m database.initial.create_tables
```

## 4. Correr el servidor

### Desarrollo (local)
```bash
uv run uvicorn main:app --reload --env-file .env.dev
```

### Producción (VPS)
```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --env-file .env.prod
```
O con Gunicorn:
```bash
env $(cat .env.prod | xargs) gunicorn -w 1 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
```

## 5. Actualización de código en VPS
```bash
git fetch origin
git checkout main
git reset --hard origin/main
```