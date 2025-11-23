from sqlalchemy.orm import Session
from models.document import Document
import json

def save_document(db: Session, metadata, file_path, detected_names=None, uploaded_by=None, is_approved=False):
    document = Document(
        case_number=metadata.get("case_number"),
        case_year=metadata.get("case_year"),
        crime=metadata.get("crime"),
        verdict=metadata.get("verdict"),
        cited_jurisprudence=json.dumps(
            metadata.get("cited_jurisprudence", []), ensure_ascii=False
        ),
        file_path=file_path,
        detected_names=json.dumps(detected_names or [], ensure_ascii=False),  # Guarda los nombres como JSON
        uploaded_by=uploaded_by,
        is_approved=is_approved
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document