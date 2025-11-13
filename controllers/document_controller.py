from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse, FileResponse
import time
import os
from datetime import datetime
from sqlalchemy.orm import Session
from database.database import SessionLocal
from models.document import Document
from services.file_service import save_uploaded_file
from services.pdf.pdf_service import extract_text_from_pdf
from services.document.metadata_service import extract_metadata
from services.document.document_service import save_document
from services.document.embedding_service import save_document_embeddings
from services.pdf.spacy_service import extraer_personas_ambos_casos
from services.pdf.name_filter_service import (
    filtrar_nombres,
    cargar_dataset_nombres,
    normalizar_nombre,
)
from services.pdf.censorship_service import censurar_pdf_con_rectangulos

router = APIRouter()

@router.post("/analyze_pdf")
async def analyze_pdf(file: UploadFile = File(...)):
    total_start = time.time()

    # Save file to disk
    file_path = save_uploaded_file(file)

    # Extract text from PDF
    text = extract_text_from_pdf(open(file_path, "rb"))

    # Extract metadata
    gemini_start = time.time()
    metadata = extract_metadata(text)
    gemini_duration = time.time() - gemini_start

    # Extract and filter names
    names_start = time.time()
    personas_minusculas, personas_normal = extraer_personas_ambos_casos(file_path)
    todas_personas = sorted(set(personas_minusculas + personas_normal))
    
    # Deduplicate by normalization
    personas_normalizadas = {}
    for persona in todas_personas:
        persona_norm = normalizar_nombre(persona)
        if persona_norm not in personas_normalizadas:
            personas_normalizadas[persona_norm] = persona
    todas_personas_unicas = list(personas_normalizadas.values())
    
    # Filter names
    dataset_info = cargar_dataset_nombres("data/name_surnames_normalizated.csv")
    resultado = filtrar_nombres(
        todas_personas_unicas,
        dataset_info,
        personas_minusculas,
        personas_normal,
        umbral_minimo=8
    )
    nombres_a_censurar = resultado["nombres_originales_a_censurar"]
    names_duration = time.time() - names_start

    # Censor PDF and save with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    censored_filename = f"{os.path.splitext(file.filename)[0]}_censurado_{timestamp}.pdf"
    censored_path = os.path.join("uploaded_docs", censored_filename)
    
    censurar_pdf_con_rectangulos(file_path, censored_path, nombres_a_censurar)

    # Save document to PostgreSQL with censored PDF path and detected names
    db: Session = SessionLocal()
    document = save_document(
        db, 
        metadata, 
        censored_path,
        detected_names=nombres_a_censurar
    )
    db.close()

    # Save embeddings to Qdrant
    embedding_start = time.time()
    num_chunks, embedding_msg = _process_embeddings(document.id, text)
    embedding_duration = time.time() - embedding_start

    total_duration = time.time() - total_start

    return JSONResponse(
        content={
            "metadata": metadata,
            "document_id": document.id,
            "file_url": f"/documents/download/{document.id}",
            "detected_names": nombres_a_censurar,
            "total_names_detected": len(todas_personas_unicas),
            "total_names_censored": len(nombres_a_censurar),
            "gemini_processing_time_seconds": round(gemini_duration, 3),
            "name_extraction_time_seconds": round(names_duration, 3),
            "embedding_processing_time_seconds": round(embedding_duration, 3),
            "total_processing_time_seconds": round(total_duration, 3),
            "msg": f"Document analyzed, censored and saved | {embedding_msg}",
        }
    )

def _process_embeddings(document_id, text):
    try:
        num_chunks = save_document_embeddings(document_id, text)
        return num_chunks, f"✅ {num_chunks} chunks saved in Qdrant"
    except Exception as e:
        print(f"Error saving embeddings: {str(e)}")
        return 0, f"⚠️ Error saving embeddings: {str(e)}"

@router.get("/documents/download/{document_id}")
def download_document(document_id: int):
    db: Session = SessionLocal()
    doc = db.query(Document).filter(Document.id == document_id).first()
    db.close()
    
    if not doc or not doc.file_path or not os.path.exists(doc.file_path):
        return JSONResponse(status_code=404, content={"msg": "File not found"})
    
    return FileResponse(
        doc.file_path,
        media_type="application/pdf",
        filename=os.path.basename(doc.file_path),
    )