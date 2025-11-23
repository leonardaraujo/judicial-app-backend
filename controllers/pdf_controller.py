from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles

router = APIRouter()

# Montar la carpeta 'uploaded_docs' para servir archivos PDF estáticos
def include_static(app):
    app.mount("/static", StaticFiles(directory="uploaded_docs"), name="static")