
# Correr el servidor
uv run uvicorn main:app --reload

# Configuracion inicial de tablas
uv run python create_tables.py