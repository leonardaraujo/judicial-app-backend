from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database.database import SessionLocal
from models.document import Document
from pydantic import BaseModel
import json
import os
router = APIRouter(prefix="/documents", tags=["documents"])

class DocumentBase(BaseModel):
    id: int
    case_number: str = ""
    case_year: str = ""
    crime: str = ""
    verdict: str = ""
    cited_jurisprudence: list = []
    file_path: str = ""

class DocumentUpdate(DocumentBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=list[DocumentBase])
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).all()
    result = []
    for doc in docs:
        try:
            cited_juris = json.loads(doc.cited_jurisprudence or "[]")
            if not isinstance(cited_juris, list):
                cited_juris = []
        except Exception:
            cited_juris = []
        result.append({
            "id": doc.id,
            "case_number": doc.case_number or "",
            "case_year": doc.case_year or "",
            "crime": doc.crime or "",
            "verdict": doc.verdict or "",
            "cited_jurisprudence": cited_juris,
            "file_path": doc.file_path or ""
        })
    return result

@router.get("/{document_id}")
def get_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    try:
        cited_juris = json.loads(doc.cited_jurisprudence or "[]")
        if not isinstance(cited_juris, list):
            cited_juris = []
    except Exception:
        cited_juris = []
    user = doc.uploader  # gracias al relationship en el modelo Document
    return {
        "id": doc.id,
        "uploaded_by": str(doc.uploaded_by) if doc.uploaded_by else None,
        "file_path": doc.file_path or "",
        "created_at": doc.created_at,
        "case_number": doc.case_number or "",
        "case_year": doc.case_year or "",
        "crime": doc.crime or "",
        "verdict": doc.verdict or "",
        "cited_jurisprudence": cited_juris,
        "resume": doc.resume or "",
        "user": {
            "first_name": user.first_name if user else None,
            "last_name": user.last_name if user else None,
            "email": user.email if user else None
        }
    }

@router.put("/{document_id}", response_model=DocumentBase)
def update_document(document_id: int, document: DocumentUpdate, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    doc.case_number = document.case_number
    doc.case_year = document.case_year
    doc.crime = document.crime
    doc.verdict = document.verdict
    doc.cited_jurisprudence = json.dumps(document.cited_jurisprudence, ensure_ascii=False)
    doc.file_path = document.file_path
    db.commit()
    db.refresh(doc)
    return {
        "id": doc.id,
        "case_number": doc.case_number,
        "case_year": doc.case_year,
        "crime": doc.crime,
        "verdict": doc.verdict,
        "cited_jurisprudence": json.loads(doc.cited_jurisprudence or "[]"),
        "file_path": doc.file_path
    }

@router.delete("/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    # Eliminar el archivo físico si existe
    file_path = doc.file_path
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error eliminando archivo: {e}")
    db.delete(doc)
    db.commit()
    return {"msg": "Documento y archivo eliminados correctamente"}