"""Tests for the RAG module."""

import tempfile
from pathlib import Path

import pytest

from src.rag import (
    MarkdownChunker,
    Chunk,
    EmbeddingService,
    VectorStore,
    Retriever,
    ingest_knowledge_base,
)


class TestMarkdownChunker:
    """Tests for the markdown chunker."""
    
    def test_chunk_simple_document(self, tmp_path):
        """Test chunking a simple markdown document."""
        # Create test file
        test_md = tmp_path / "test.md"
        test_md.write_text("""# Test Document

This is the introduction paragraph with enough content to pass the minimum chunk size threshold. It contains details about the test.

## Section 1

Content for section 1. This section has important information about testing. We need to make sure this is long enough to be included as a chunk.

## Section 2

Content for section 2. Another section with different information that should be chunked separately from section 1.
""")
        
        chunker = MarkdownChunker(max_chunk_size=500, min_chunk_size=50)
        chunks = list(chunker.chunk_file(test_md))
        
        assert len(chunks) >= 2
        assert chunks[0].title == "Test Document"
        assert all(isinstance(c, Chunk) for c in chunks)
    
    def test_chunk_respects_max_size(self, tmp_path):
        """Test that chunks don't exceed max size (approximately)."""
        # Create content with distinct sentences that can be split
        sentences = ["This is sentence number " + str(i) + "." for i in range(100)]
        content = "# Title\n\n" + " ".join(sentences)
        
        test_md = tmp_path / "test.md"
        test_md.write_text(content)
        
        chunker = MarkdownChunker(max_chunk_size=500, min_chunk_size=50)
        chunks = list(chunker.chunk_file(test_md))
        
        # At least some chunks should be created
        assert len(chunks) >= 1
        # Most chunks should be under the max size (some tolerance for edge cases)
        for chunk in chunks:
            assert len(chunk.content) <= 600  # Allow some flexibility
    
    def test_extract_category_from_path(self, tmp_path):
        """Test category extraction from file path."""
        # Create nested structure matching expected format
        tools_dir = tmp_path / "tools" / "3d_printing"
        tools_dir.mkdir(parents=True)
        test_md = tools_dir / "printer.md"
        test_md.write_text("""# Printer

Some content about the printer that is long enough to pass the minimum chunk size threshold for testing purposes.
""")
        
        chunker = MarkdownChunker(min_chunk_size=50)
        chunks = list(chunker.chunk_file(test_md))
        
        assert len(chunks) >= 1
        assert chunks[0].metadata["category"] == "3d_printing"



class TestEmbeddingService:
    """Tests for the embedding service."""
    
    def test_embed_single_text(self):
        """Test embedding a single text."""
        service = EmbeddingService()
        embedding = service.embed("Hello world")
        
        assert embedding.shape == (1, 384)
    
    def test_embed_multiple_texts(self):
        """Test embedding multiple texts."""
        service = EmbeddingService()
        embeddings = service.embed(["Hello", "World", "Test"])
        
        assert embeddings.shape == (3, 384)
    
    def test_embed_query(self):
        """Test embedding a query (returns 1D)."""
        service = EmbeddingService()
        embedding = service.embed_query("test query")
        
        assert embedding.shape == (384,)


class TestVectorStore:
    """Tests for the vector store."""
    
    def test_add_and_search(self, tmp_path):
        """Test adding chunks and searching."""
        store = VectorStore(persist_directory=tmp_path / "test_store")
        
        # Create test chunks
        chunks = [
            Chunk(
                content="3D printers use PLA and ABS filament",
                source="test.md",
                title="3D Printing",
                section="Materials",
                chunk_index=0,
                metadata={"category": "3d_printing"}
            ),
            Chunk(
                content="Laser cutters can cut wood and acrylic",
                source="test.md",
                title="Laser Cutting",
                section="Materials",
                chunk_index=1,
                metadata={"category": "laser_cutting"}
            ),
        ]
        
        store.add_chunks(chunks)
        assert store.count() == 2
        
        # Search
        results = store.search("What filament can I use?", n_results=1)
        assert len(results) == 1
        assert "PLA" in results[0]["content"]
    
    def test_filter_by_category(self, tmp_path):
        """Test filtering search by category."""
        store = VectorStore(persist_directory=tmp_path / "test_store")
        
        chunks = [
            Chunk(
                content="3D printer content",
                source="test.md",
                title="3D",
                section="Test",
                chunk_index=0,
                metadata={"category": "3d_printing"}
            ),
            Chunk(
                content="Laser cutter content",
                source="test.md",
                title="Laser",
                section="Test",
                chunk_index=1,
                metadata={"category": "laser_cutting"}
            ),
        ]
        
        store.add_chunks(chunks)
        
        results = store.search("content", n_results=2, filter_category="laser_cutting")
        assert len(results) == 1
        assert "Laser" in results[0]["content"]


class TestRetriever:
    """Tests for the retriever."""
    
    def test_search_returns_results(self, tmp_path):
        """Test that search returns RetrievalResult objects."""
        # Set up store with test data
        store = VectorStore(persist_directory=tmp_path / "test_store")
        chunks = [
            Chunk(
                content="The ICL is located in Plank Gym building",
                source="test.md",
                title="ICL Info",
                section="Location",
                chunk_index=0,
                metadata={"category": "general"}
            )
        ]
        store.add_chunks(chunks)
        
        # Create retriever with this store directly
        retriever = Retriever(store=store, relevance_threshold=0.0)
        
        results = retriever.search("Where is the ICL?", include_low_relevance=True)
        assert len(results) >= 1
        assert results[0].title == "ICL Info"
        assert results[0].relevance > 0
    
    def test_get_context(self, tmp_path):
        """Test getting formatted context for LLM."""
        store = VectorStore(persist_directory=tmp_path / "test_store")
        chunks = [
            Chunk(
                content="Important information here about the Innovation and Creativity Lab. The lab provides various tools and resources for students to explore creative projects.",
                source="test.md",
                title="ICL Info",
                section="Main",
                chunk_index=0,
                metadata={"category": "general"}
            )
        ]
        store.add_chunks(chunks)
        
        # Pass store directly to avoid singleton issues
        retriever = Retriever(store=store, relevance_threshold=0.0)
        context = retriever.get_context("ICL information")
        
        assert "Important information" in context


class TestIntegration:
    """Integration tests for the full RAG pipeline."""
    
    def test_ingest_and_retrieve(self, tmp_path):
        """Test the full ingest -> retrieve pipeline."""
        # Create a mini knowledge base
        kb_path = tmp_path / "knowledge_base"
        tools_dir = kb_path / "tools" / "test_category"
        tools_dir.mkdir(parents=True)
        
        test_md = tools_dir / "test_tool.md"
        test_md.write_text("""# Test Tool

**Type:** Testing Equipment for Quality Assurance

## Overview

This is a test tool for unit testing the RAG system. It contains enough content to pass the minimum chunk size threshold. The test tool is designed to verify that the ingestion and retrieval pipeline works correctly.

## Usage Instructions

Follow these detailed steps to use the test tool properly:

1. First, prepare the test environment by setting up all necessary dependencies
2. Next, configure the tool according to your specific requirements
3. Then run the test sequence and observe the results carefully
4. Finally, review the output and verify everything works as expected
""")
        
        # Ingest
        store_path = tmp_path / "vector_store"
        stats = ingest_knowledge_base(
            kb_path=kb_path,
            store_path=store_path
        )
        
        assert stats["files_processed"] >= 1
        assert stats["chunks_stored"] >= 1
        
        # Retrieve
        retriever = Retriever(store_path=store_path)
        results = retriever.search("test tool usage", include_low_relevance=True)
        
        assert len(results) >= 1
        assert "Test Tool" in results[0].title

