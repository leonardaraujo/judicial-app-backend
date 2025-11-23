from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database.database import SessionLocal
from models.document import Document
from services.qdrant.embeddings_service import get_embedding
from services.qdrant.qdrant_service import search_embeddings
import json

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/search")
def search_documents(
    query: str = Query(..., description="Palabra o frase a buscar"),
    top_k: int = 5,
    db: Session = Depends(get_db)
):
    embedding = get_embedding(query)
    results = search_embeddings(embedding, top_k=top_k)
    grouped = {}

    for r in results:
        item = r.model_dump() if hasattr(r, "model_dump") else dict(r)
        doc_id = None
        if "payload" in item and isinstance(item["payload"], dict):
            doc_id = item["payload"].get("document_id")
        if not doc_id:
            continue

        score = item.get("score")
        chunk = {
            "score": score,
            "chunk_index": item.get("payload", {}).get("chunk_index"),
            "text": item.get("payload", {}).get("text"),
        }

        # Solo guardar el chunk con mayor score por documento
        if doc_id not in grouped or score > grouped[doc_id]["chunk"]["score"]:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if doc:
                try:
                    cited_juris = json.loads(doc.cited_jurisprudence or "[]")
                    if not isinstance(cited_juris, list):
                        cited_juris = []
                except Exception:
                    cited_juris = []
                try:
                    detected_names = json.loads(doc.detected_names or "[]")
                    if not isinstance(detected_names, list):
                        detected_names = []
                except Exception:
                    detected_names = []
                metadata = {
                    "id": doc.id,
                    "case_number": doc.case_number or "",
                    "case_year": doc.case_year or "",
                    "crime": doc.crime or "",
                    "verdict": doc.verdict or "",
                    "cited_jurisprudence": cited_juris,
                }
            else:
                metadata = None
            grouped[doc_id] = {
                "document_id": doc_id,
                "metadata": metadata,
                "chunk": chunk
            }

    response = list(grouped.values())
    return JSONResponse(content={"results": response}) 