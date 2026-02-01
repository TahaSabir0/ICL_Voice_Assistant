"""
RAG (Retrieval-Augmented Generation) module for ICL Voice Assistant.

Components:
- chunker: Split markdown documents into semantic chunks
- embeddings: Generate embeddings using sentence-transformers
- vectorstore: ChromaDB-based vector storage
- ingest: Load and index knowledge base
- retriever: High-level search interface
"""

from .chunker import MarkdownChunker, Chunk
from .embeddings import EmbeddingService, get_embedding_service
from .vectorstore import VectorStore, get_vector_store
from .ingest import ingest_knowledge_base
from .retriever import Retriever, RetrievalResult, get_retriever

__all__ = [
    # Chunker
    "MarkdownChunker",
    "Chunk",
    # Embeddings
    "EmbeddingService",
    "get_embedding_service",
    # Vector Store
    "VectorStore",
    "get_vector_store",
    # Ingestion
    "ingest_knowledge_base",
    # Retrieval
    "Retriever",
    "RetrievalResult",
    "get_retriever",
]
