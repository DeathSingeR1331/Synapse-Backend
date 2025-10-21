import uuid
from typing import List, Optional
from qdrant_client import AsyncQdrantClient, models
from src.core.config import settings
from src.services.interfaces._vector_store import IVectorStoreService


class RealVectorStoreService(IVectorStoreService):
    """
    Real implementation of the vector store service using Qdrant.
    This service is responsible for vector search and storage.
    """

    _collection_name: str = "synapse_memory"

    def __init__(self):
        self._client = AsyncQdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            grpc_port=settings.QDRANT_GRPC_PORT,
            prefer_grpc=True,
        )

    async def initialize_store(self):
        """Ensures the required collection exists in Qdrant."""
        try:
            await self._client.get_collection(collection_name=self._collection_name)
            print(f"Vector collection '{self._collection_name}' already exists.")
        except Exception:
            print(f"Vector collection '{self._collection_name}' not found. Creating...")
            await self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config=models.VectorParams(
                    size=768,  # Size for BGE embedding model
                    distance=models.Distance.COSINE,
                ),
            )
            print("Collection created successfully.")

    async def add_document_to_memory(
        self, doc_id: uuid.UUID, embedding: List[float], metadata: dict
    ):
        """Adds or updates a single document vector in the Qdrant collection."""
        point = models.PointStruct(
            id=str(doc_id),
            vector=embedding,
            payload=metadata
        )
        await self._client.upsert(
            collection_name=self._collection_name,
            points=[point],
            wait=True
        )

    async def query_similar_documents(
        self,
        embedding: List[float],
        top_k: int = 5,
        metadata_filter: Optional[dict] = None,
    ) -> List[dict]:
        """Queries Qdrant for documents similar to the given embedding."""
        qdrant_filter = models.Filter(**metadata_filter) if metadata_filter else None
        search_result = await self._client.search(
            collection_name=self._collection_name,
            query_vector=embedding,
            query_filter=qdrant_filter,
            limit=top_k,
            with_payload=True,
        )
        return [
            {"id": point.id, "score": point.score, "payload": point.payload}
            for point in search_result
        ]

    async def close(self):
        """Closes the connection to the Qdrant client."""
        await self._client.close()