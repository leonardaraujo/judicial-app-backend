from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from database.database import SessionLocal
from models.document import Document
import json
import os
from services.document.resume_document_service import summarize_document

router = APIRouter()

def censurar_nombres_en_texto(texto, nombres):
    for nombre in nombres:
        texto = texto.replace(nombre, "[censurado]")
    return texto

@router.get("/ia/{document_id}/resume")
def resumir_documento(document_id: int):
    db: Session = SessionLocal()
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        db.close()
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    # Si ya existe resumen, devolverlo
    if doc.resume:
        result = {"document_id": doc.id, "resume": doc.resume, "from_cache": True}
        db.close()
        return result

    # Extraer texto del documento PDF
    from services.pdf.pdf_service import extract_text_from_pdf
    if not doc.file_path or not os.path.exists(doc.file_path):
        db.close()
        raise HTTPException(status_code=404, detail="Archivo PDF no encontrado")
    with open(doc.file_path, "rb") as f:
        texto = extract_text_from_pdf(f)

    # Censurar nombres detectados
    nombres = []
    try:
        nombres = json.loads(doc.detected_names or "[]")
    except Exception:
        nombres = []
    texto_censurado = censurar_nombres_en_texto(texto, nombres)

    # Llamar al servicio real de resumen con IA
    resumen = summarize_document(texto_censurado)

    # Guardar el resumen en la base de datos
    doc.resume = resumen
    db.commit()
    # Guarda los datos antes de cerrar la sesión
    result = {"document_id": doc.id, "resume": resumen, "from_cache": False}
    db.close()

    return result