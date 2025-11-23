from fastapi import APIRouter, File, UploadFile
import json
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
from .auth_controller import get_current_user
from fastapi import Depends
import uuid
from .auth_controller import get_current_user

router = APIRouter()


@router.post("/analyze_pdf")
async def analyze_pdf(
    file: UploadFile = File(...), current_user=Depends(get_current_user)
):
    total_start = time.time()

    # Save file to disk
    file_path = save_uploaded_file(file)

    # Extract text from PDF
    text = extract_text_from_pdf(open(file_path, "rb"))

    # Extract metadata (Gemini)
    gemini_start = time.time()
    gemini_success = True
    try:
        metadata = extract_metadata(text)
    except Exception as e:
        gemini_success = False
        metadata = {
            "case_number": "",
            "case_year": "",
            "crime": "",
            "verdict": "",
            "cited_jurisprudence": "",
        }
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
        umbral_minimo=8,
    )
    nombres_a_censurar = resultado["nombres_originales_a_censurar"]
    names_duration = time.time() - names_start

    # Censor PDF and save with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    censored_filename = f"{timestamp}.pdf"
    censored_path = os.path.join("uploaded_docs", "approved", censored_filename)

    censurar_pdf_con_rectangulos(file_path, censored_path, nombres_a_censurar)

    # Save document to PostgreSQL with censored PDF path and detected names
    db: Session = SessionLocal()
    user_id = current_user["user_id"]
    if isinstance(user_id, str):
        user_id = uuid.UUID(user_id)
    document = save_document(
        db,
        metadata,
        censored_path,
        detected_names=nombres_a_censurar,
        uploaded_by=user_id,
        is_approved=True,
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
            "msg": (
                f"Document analyzed, censored and saved | {embedding_msg} | "
                + (
                    "✅ Metadatos extraídos correctamente"
                    if gemini_success
                    else "⚠️ Error extrayendo metadatos, campos vacíos"
                )
            ),
            "gemini_success": gemini_success,
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


@router.post("/upload_pending")
async def upload_pending_document(
    file: UploadFile = File(...), current_user=Depends(get_current_user)
):
    os.makedirs("uploaded_docs/pending_to_approve", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pending_filename = f"{timestamp}.pdf"
    pending_path = os.path.join("uploaded_docs", "pending_to_approve", pending_filename)

    with open(pending_path, "wb") as f:
        f.write(await file.read())

    db: Session = SessionLocal()

    # Convierte a UUID si es necesario
    user_id = current_user["user_id"]
    if isinstance(user_id, str):
        user_id = uuid.UUID(user_id)

    document = save_document(
        db,
        metadata={},
        file_path=pending_path,
        detected_names=[],
        is_approved=False,
        uploaded_by=user_id,  # ✅ Ahora es UUID
    )
    db.close()

    return JSONResponse(
        content={
            "msg": "Documento subido y pendiente de aprobación",
            "document_id": document.id,
            "file_path": pending_path,
        }
    )


@router.get("/documents/pending")
def get_pending_documents():
    db: Session = SessionLocal()
    documents = db.query(Document).filter(Document.is_approved == False).all()
    results = []
    for doc in documents:
        user = doc.uploader  # gracias al relationship en el modelo Document
        results.append(
            {
                "id": doc.id,
                "uploaded_by": str(doc.uploaded_by),
                "file_path": doc.file_path,
                "created_at": doc.created_at,
                "user": {
                    "first_name": user.first_name if user else None,
                    "last_name": user.last_name if user else None,
                    "email": user.email if user else None,
                },
            }
        )
    db.close()
    return results


@router.delete("/documents/reject/{document_id}")
def reject_document(document_id: int):
    db: Session = SessionLocal()
    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.is_approved == False)
        .first()
    )
    if not document:
        db.close()
        return JSONResponse(
            status_code=404, content={"msg": "Documento pendiente no encontrado"}
        )

    file_path = document.file_path
    # Eliminar el archivo si existe
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        db.close()
        return JSONResponse(
            status_code=500, content={"msg": f"Error eliminando archivo: {e}"}
        )

    # Eliminar el registro de la base de datos
    db.delete(document)
    db.commit()
    db.close()
    return JSONResponse(
        content={"msg": "Documento rechazado y eliminado correctamente"}
    )


@router.post("/documents/approve/{document_id}")
def approve_document(document_id: int):
    db: Session = SessionLocal()
    try:
        document = (
            db.query(Document)
            .filter(Document.id == document_id, Document.is_approved == False)
            .first()
        )
        if not document:
            return JSONResponse(
                status_code=404, content={"msg": "Documento pendiente no encontrado"}
            )

        file_path = document.file_path
        if not os.path.exists(file_path):
            return JSONResponse(
                status_code=404, content={"msg": "Archivo PDF no encontrado"}
            )

        # Procesar PDF y extraer info
        try:
            with open(file_path, "rb") as f:
                text = extract_text_from_pdf(f)
        except Exception as e:
            return JSONResponse(
                status_code=500, content={"msg": f"Error extrayendo texto del PDF: {e}"}
            )

        try:
            metadata = extract_metadata(text)
            gemini_success = True
        except Exception as e:
            gemini_success = False
            metadata = {
                "case_number": "",
                "case_year": "",
                "crime": "",
                "verdict": "",
                "cited_jurisprudence": [],
            }

        # Extraer y filtrar nombres
        try:
            personas_minusculas, personas_normal = extraer_personas_ambos_casos(
                file_path
            )
            todas_personas = sorted(set(personas_minusculas + personas_normal))
            personas_normalizadas = {}
            for persona in todas_personas:
                persona_norm = normalizar_nombre(persona)
                if persona_norm not in personas_normalizadas:
                    personas_normalizadas[persona_norm] = persona
            todas_personas_unicas = list(personas_normalizadas.values())
            dataset_info = cargar_dataset_nombres("data/name_surnames_normalizated.csv")
            resultado = filtrar_nombres(
                todas_personas_unicas,
                dataset_info,
                personas_minusculas,
                personas_normal,
                umbral_minimo=8,
            )
            nombres_a_censurar = resultado["nombres_originales_a_censurar"]
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"msg": f"Error extrayendo o filtrando nombres: {e}"},
            )

        # Censurar PDF y mover a carpeta de aprobados
        try:
            os.makedirs("uploaded_docs/approved", exist_ok=True)
            approved_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            approved_path = os.path.join("uploaded_docs", "approved", approved_filename)
            censurar_pdf_con_rectangulos(file_path, approved_path, nombres_a_censurar)
        except Exception as e:
            return JSONResponse(
                status_code=500, content={"msg": f"Error censurando PDF: {e}"}
            )

        # Eliminar el archivo pendiente
        try:
            os.remove(file_path)
        except Exception as e:
            # No es crítico, solo advertencia
            print(f"Advertencia: No se pudo eliminar el archivo pendiente: {e}")

        # Actualizar documento en la base de datos
        try:
            document.file_path = approved_path
            document.is_approved = True
            document.detected_names = json.dumps(nombres_a_censurar, ensure_ascii=False)
            document.case_number = metadata.get("case_number")
            document.case_year = metadata.get("case_year") or metadata.get("year") or ""
            document.crime = metadata.get("crime")
            document.verdict = metadata.get("verdict")
            cited_jurisprudence = metadata.get("cited_jurisprudence", [])
            if not cited_jurisprudence:
                cited_jurisprudence = []
            document.cited_jurisprudence = json.dumps(
                cited_jurisprudence, ensure_ascii=False
            )
            db.commit()
        except Exception as e:
            db.rollback()
            return JSONResponse(
                status_code=500,
                content={
                    "msg": f"Error actualizando documento en la base de datos: {e}"
                },
            )

        # Guardar embeddings
        try:
            num_chunks = save_document_embeddings(document.id, text)
            embedding_msg = f"✅ {num_chunks} chunks saved in Qdrant"
        except Exception as e:
            embedding_msg = f"⚠️ Error saving embeddings: {str(e)}"

        return JSONResponse(
            content={
                "metadata": metadata,
                "document_id": document.id,
                "file_url": f"/documents/download/{document.id}",
                "detected_names": nombres_a_censurar,
                "total_names_detected": len(todas_personas_unicas),
                "total_names_censored": len(nombres_a_censurar),
                "msg": (
                    f"Documento aprobado, censurado y guardado | {embedding_msg} | "
                    + (
                        "✅ Metadatos extraídos correctamente"
                        if gemini_success
                        else "⚠️ Error extrayendo metadatos, campos vacíos"
                    )
                ),
                "gemini_success": gemini_success,
            }
        )
    finally:
        db.close()
