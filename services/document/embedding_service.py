from services.qdrant.qdrant_service import ensure_collection, upsert_embedding
from services.qdrant.embeddings_service import get_embedding

def save_document_embeddings(document_id, text, chunk_size=250):
    ensure_collection()
    palabras = text.split()
    chunks = [" ".join(palabras[i:i+chunk_size]) for i in range(0, len(palabras), chunk_size)]
    for idx, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        point_id = int(f"{document_id}{idx}")
        payload = {
            "document_id": int(document_id),
            "chunk_index": int(idx),
            "text": chunk[:300],
            "full_text": chunk
        }
        upsert_embedding(point_id, embedding, payload)
    return len(chunks)