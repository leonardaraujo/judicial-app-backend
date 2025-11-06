FROM python:3.12

WORKDIR /app

# Copiamos solo los archivos de configuración primero para aprovechar la cache de Docker
COPY pyproject.toml uv.lock ./

# Instalamos uv
RUN pip install --upgrade pip && pip install uv

# Instalamos dependencias del proyecto usando el pyproject.toml
RUN uv pip install --system --requirements pyproject.toml

# Ahora copiamos el resto del código
COPY . .

# Comando por defecto: crear tablas y lanzar servidor
CMD uv run python -m database.initial.create_tables && uv run uvicorn main:app --host 0.0.0.0 --port 8000