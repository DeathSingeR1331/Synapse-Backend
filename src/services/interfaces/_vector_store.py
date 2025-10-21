# Synapse-Backend/src/services/interfaces/_vector_store.py

import uuid
from abc import ABC, abstractmethod
from typing import List, Optional

class IVectorStoreService(ABC):
    """Abstract interface for a vector store service."""

    @abstractmethod
    async def initialize_store(self) -> None:
        """Ensures the required storage (e.g., a collection) exists."""
        raise NotImplementedError

    @abstractmethod
    async def query_similar_documents(
        self,
        embedding: List[float],
        top_k: int = 5,
        metadata_filter: Optional[dict] = None,
    ) -> List[dict]:
        """Queries the vector store for documents similar to the given embedding."""
        raise NotImplementedError

    @abstractmethod
    async def add_document_to_memory(
        self, doc_id: uuid.UUID, embedding: List[float], metadata: dict
    ) -> None:
        """Adds or updates a single document in the vector store."""
        raise NotImplementedError