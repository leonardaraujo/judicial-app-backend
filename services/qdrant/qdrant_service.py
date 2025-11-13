import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))

qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
collection_name = "judicial_chunks"
VECTOR_SIZE = 384

def ensure_collection():
    if collection_name not in [c.name for c in qdrant.get_collections().collections]:
        qdrant.create_collection(
            collection_name=collection_name,
            vectors_config=qdrant_models.VectorParams(size=VECTOR_SIZE, distance="Cosine")
        )

def upsert_embedding(doc_id, emb, payload):
    qdrant.upsert(
        collection_name=collection_name,
        points=[
            qdrant_models.PointStruct(
                id=doc_id,
                vector=emb,
                payload=payload 
            )
        ]
    )

def search_embeddings(query_emb, top_k=3):
    return qdrant.search(
        collection_name=collection_name,
        query_vector=query_emb,
        limit=top_k
    )