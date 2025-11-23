from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

client = QdrantClient(host="localhost", port=6333)

collection_name = "judicial_chunks"

# Cambia el tamaño a 384 para que coincida con tu servicio
VECTOR_SIZE = 384

if collection_name not in [c.name for c in client.get_collections().collections]:
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
    )
    print(f"Collection '{collection_name}' created.")
else:
    print(f"Collection '{collection_name}' already exists.")