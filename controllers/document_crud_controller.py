from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database.database import SessionLocal
from models.document import Document
from pydantic import BaseModel
import json

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
        result.append({
            "id": doc.id,  # <-- AGREGA ESTA LÍNEA
            "case_number": doc.case_number,
            "case_year": doc.case_year,
            "crime": doc.crime,
            "verdict": doc.verdict,
            "cited_jurisprudence": json.loads(doc.cited_jurisprudence or "[]"),
            "file_path": doc.file_path
        })
    return result

@router.get("/{document_id}", response_model=DocumentBase)
def get_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return {
        "id": doc.id,
        "case_number": doc.case_number,
        "case_year": doc.case_year,
        "crime": doc.crime,
        "verdict": doc.verdict,
        "cited_jurisprudence": json.loads(doc.cited_jurisprudence or "[]"),
        "file_path": doc.file_path
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
    db.delete(doc)
    db.commit()
    return {"msg": "Documento eliminado"}