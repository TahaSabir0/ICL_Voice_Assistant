"""
Embedding service using sentence-transformers.

Generates embeddings for text chunks using all-MiniLM-L6-v2.
"""

from typing import Union

import numpy as np


class EmbeddingService:
    """
    Generate embeddings using sentence-transformers.
    
    Uses all-MiniLM-L6-v2 by default:
    - Fast (14k sentences/sec on GPU)
    - Small (80MB)
    - Good quality for semantic search
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
    
    @property
    def model(self):
        """Lazy load the model."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            print(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            print(f"Embedding model loaded. Dimension: {self._model.get_sentence_embedding_dimension()}")
        return self._model
    
    def embed(self, texts: Union[str, list[str]]) -> np.ndarray:
        """
        Generate embeddings for text(s).
        
        Args:
            texts: Single string or list of strings
            
        Returns:
            numpy array of embeddings
        """
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 10
        )
        
        return embeddings
    
    def embed_query(self, query: str) -> np.ndarray:
        """Generate embedding for a search query."""
        return self.embed(query)[0]
    
    def embed_documents(self, documents: list[str]) -> np.ndarray:
        """Generate embeddings for multiple documents."""
        return self.embed(documents)
    
    @property
    def embedding_dimension(self) -> int:
        """Get the embedding dimension."""
        return self.model.get_sentence_embedding_dimension()
    
    def unload(self):
        """Unload the model to free memory."""
        if self._model is not None:
            del self._model
            self._model = None
            print("Embedding model unloaded")


# Global singleton instance
_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the global embedding service."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
