"""
Vector store using ChromaDB.

Provides storage and retrieval of embedded document chunks.
"""

from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings

from .chunker import Chunk
from .embeddings import EmbeddingService, get_embedding_service


class VectorStore:
    """
    ChromaDB-based vector store for RAG retrieval.
    
    Stores document chunks with embeddings and metadata,
    supports semantic similarity search.
    """
    
    def __init__(
        self,
        persist_directory: Optional[Path] = None,
        collection_name: str = "icl_knowledge_base",
        embedding_service: Optional[EmbeddingService] = None
    ):
        self.collection_name = collection_name
        self.embedding_service = embedding_service or get_embedding_service()
        
        # Configure ChromaDB
        if persist_directory:
            persist_directory = Path(persist_directory)
            persist_directory.mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(
                path=str(persist_directory),
                settings=Settings(anonymized_telemetry=False)
            )
        else:
            self.client = chromadb.Client(
                settings=Settings(anonymized_telemetry=False)
            )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
    
    def add_chunks(self, chunks: list[Chunk], batch_size: int = 100) -> int:
        """
        Add chunks to the vector store.
        
        Args:
            chunks: List of Chunk objects to add
            batch_size: Number of chunks to process at once
            
        Returns:
            Number of chunks added
        """
        if not chunks:
            return 0
        
        total_added = 0
        
        # Process in batches for memory efficiency
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            # Prepare data
            ids = [f"{chunk.source}_{chunk.chunk_index}" for chunk in batch]
            documents = [chunk.content for chunk in batch]
            metadatas = [chunk.to_dict() for chunk in batch]
            
            # Remove 'content' from metadata (it's stored as document)
            for meta in metadatas:
                meta.pop('content', None)
            
            # Generate embeddings
            embeddings = self.embedding_service.embed_documents(documents)
            
            # Add to collection
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings.tolist()
            )
            
            total_added += len(batch)
            print(f"  Added batch: {total_added}/{len(chunks)} chunks")
        
        return total_added
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_category: Optional[str] = None
    ) -> list[dict]:
        """
        Search for relevant chunks.
        
        Args:
            query: Search query
            n_results: Number of results to return
            filter_category: Optional category filter
            
        Returns:
            List of result dictionaries with content, metadata, and distance
        """
        # Generate query embedding
        query_embedding = self.embedding_service.embed_query(query)
        
        # Build where filter
        where_filter = None
        if filter_category:
            where_filter = {"category": filter_category}
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                formatted.append({
                    "content": doc,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": results['distances'][0][i] if results['distances'] else None,
                    "relevance": 1 - (results['distances'][0][i] if results['distances'] else 0)
                })
        
        return formatted
    
    def delete_all(self):
        """Delete all documents from the collection."""
        # Get all IDs
        all_data = self.collection.get()
        if all_data['ids']:
            self.collection.delete(ids=all_data['ids'])
            print(f"Deleted {len(all_data['ids'])} documents")
    
    def count(self) -> int:
        """Get the number of documents in the store."""
        return self.collection.count()
    
    def get_stats(self) -> dict:
        """Get statistics about the vector store."""
        return {
            "collection_name": self.collection_name,
            "document_count": self.count(),
            "embedding_dimension": self.embedding_service.embedding_dimension
        }


# Default store path
DEFAULT_STORE_PATH = Path(__file__).parent.parent.parent / "data" / "vector_store"

_vector_store: VectorStore | None = None


def get_vector_store(persist_directory: Optional[Path] = None) -> VectorStore:
    """Get or create the global vector store."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore(
            persist_directory=persist_directory or DEFAULT_STORE_PATH
        )
    return _vector_store
