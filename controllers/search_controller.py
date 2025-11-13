from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from services.qdrant.embeddings_service import get_embedding
from services.qdrant.qdrant_service import search_embeddings

router = APIRouter()


@router.get("/search")
def search_documents(
    query: str = Query(..., description="Palabra o frase a buscar"), top_k: int = 5
):
    embedding = get_embedding(query)
    results = search_embeddings(embedding, top_k=top_k)
    results_dict = []
    for r in results:
        item = r.model_dump() if hasattr(r, "model_dump") else dict(r)
        results_dict.append(item)
    return JSONResponse(content={"results": results_dict})