
# Correr el servidor
uv run uvicorn main:app --reload

# Configuracion inicial de tablas
uv run python -m database.initial.create_tables