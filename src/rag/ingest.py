"""
Ingestion pipeline for the knowledge base.

Loads markdown files, chunks them, and stores in the vector database.
"""

from pathlib import Path
from typing import Optional

from .chunker import MarkdownChunker, Chunk
from .vectorstore import VectorStore, get_vector_store, DEFAULT_STORE_PATH


# Default knowledge base path
DEFAULT_KB_PATH = Path(__file__).parent.parent.parent / "knowledge_base"


def ingest_knowledge_base(
    kb_path: Optional[Path] = None,
    store_path: Optional[Path] = None,
    clear_existing: bool = True
) -> dict:
    """
    Ingest the entire knowledge base into the vector store.
    
    Args:
        kb_path: Path to knowledge base directory
        store_path: Path for vector store persistence
        clear_existing: Whether to clear existing data first
        
    Returns:
        Statistics about the ingestion
    """
    kb_path = Path(kb_path or DEFAULT_KB_PATH)
    store_path = Path(store_path or DEFAULT_STORE_PATH)
    
    print("=" * 60)
    print("KNOWLEDGE BASE INGESTION")
    print("=" * 60)
    print(f"Knowledge base: {kb_path}")
    print(f"Vector store: {store_path}")
    
    # Create chunker
    chunker = MarkdownChunker(
        max_chunk_size=1500,
        min_chunk_size=100
    )
    
    # Create vector store
    store = get_vector_store(store_path)
    
    if clear_existing:
        print("\nClearing existing data...")
        store.delete_all()
    
    # Collect all chunks
    print("\nChunking documents...")
    
    all_chunks: list[Chunk] = []
    files_processed = 0
    
    # Process tools directory
    tools_path = kb_path / "tools"
    if tools_path.exists():
        for chunk in chunker.chunk_directory(tools_path):
            all_chunks.append(chunk)
            if len(all_chunks) % 50 == 0:
                print(f"  {len(all_chunks)} chunks collected...")
        files_processed += len(list(tools_path.glob("**/*.md")))
    
    # Process general directory
    general_path = kb_path / "general"
    if general_path.exists():
        for chunk in chunker.chunk_directory(general_path):
            all_chunks.append(chunk)
        files_processed += len(list(general_path.glob("**/*.md")))
    
    print(f"\nTotal: {len(all_chunks)} chunks from {files_processed} files")
    
    # Add to vector store
    print("\nAdding to vector store...")
    added = store.add_chunks(all_chunks)
    
    # Get stats
    stats = store.get_stats()
    
    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)
    print(f"Files processed: {files_processed}")
    print(f"Chunks created: {len(all_chunks)}")
    print(f"Chunks stored: {added}")
    print(f"Vector store size: {stats['document_count']}")
    print(f"Embedding dimension: {stats['embedding_dimension']}")
    
    return {
        "files_processed": files_processed,
        "chunks_created": len(all_chunks),
        "chunks_stored": added,
        **stats
    }


def main():
    """Run ingestion from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest knowledge base into vector store")
    parser.add_argument(
        "--kb-path",
        type=Path,
        default=DEFAULT_KB_PATH,
        help="Path to knowledge base directory"
    )
    parser.add_argument(
        "--store-path",
        type=Path,
        default=DEFAULT_STORE_PATH,
        help="Path for vector store persistence"
    )
    parser.add_argument(
        "--no-clear",
        action="store_true",
        help="Don't clear existing data before ingestion"
    )
    
    args = parser.parse_args()
    
    ingest_knowledge_base(
        kb_path=args.kb_path,
        store_path=args.store_path,
        clear_existing=not args.no_clear
    )


if __name__ == "__main__":
    main()
