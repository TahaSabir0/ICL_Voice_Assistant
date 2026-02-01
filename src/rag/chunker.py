"""
Document chunker for the knowledge base.

Splits markdown documents into semantic chunks suitable for embedding.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass
class Chunk:
    """A chunk of text with metadata."""
    
    content: str
    source: str  # File path
    title: str  # Document title
    section: str  # Section heading
    chunk_index: int  # Position within document
    metadata: dict  # Additional metadata
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "content": self.content,
            "source": self.source,
            "title": self.title,
            "section": self.section,
            "chunk_index": self.chunk_index,
            **self.metadata
        }


class MarkdownChunker:
    """
    Chunks markdown documents using semantic boundaries.
    
    Strategy:
    1. Split on major headings (##, ###, ####)
    2. Keep paragraphs together
    3. Respect maximum chunk size
    4. Preserve context by including document title
    """
    
    def __init__(
        self,
        max_chunk_size: int = 1500,
        min_chunk_size: int = 100,
        overlap_size: int = 100
    ):
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.overlap_size = overlap_size
    
    def chunk_file(self, file_path: Path) -> Iterator[Chunk]:
        """Chunk a single markdown file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract title from first H1
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else file_path.stem
        
        # Clean the content
        content = self._clean_content(content)
        
        # Split into sections
        sections = self._split_into_sections(content)
        
        chunk_index = 0
        for section_title, section_content in sections:
            # Split section into chunks if too large
            for chunk_text in self._split_section(section_content):
                if len(chunk_text.strip()) >= self.min_chunk_size:
                    yield Chunk(
                        content=chunk_text.strip(),
                        source=str(file_path),
                        title=title,
                        section=section_title,
                        chunk_index=chunk_index,
                        metadata={
                            "category": self._extract_category(file_path),
                            "file_name": file_path.name
                        }
                    )
                    chunk_index += 1
    
    def chunk_directory(self, directory: Path, pattern: str = "**/*.md") -> Iterator[Chunk]:
        """Chunk all markdown files in a directory."""
        for file_path in directory.glob(pattern):
            if file_path.is_file():
                yield from self.chunk_file(file_path)
    
    def _clean_content(self, content: str) -> str:
        """Clean markdown content."""
        # Remove horizontal rules
        content = re.sub(r'\n---+\n', '\n\n', content)
        # Remove excessive newlines
        content = re.sub(r'\n{3,}', '\n\n', content)
        return content.strip()
    
    def _split_into_sections(self, content: str) -> list[tuple[str, str]]:
        """Split content into sections based on headings."""
        # Pattern to match headings (##, ###, ####)
        heading_pattern = re.compile(r'^(#{2,4})\s+(.+)$', re.MULTILINE)
        
        sections = []
        last_end = 0
        last_heading = "Introduction"
        
        for match in heading_pattern.finditer(content):
            # Get content before this heading
            section_content = content[last_end:match.start()].strip()
            if section_content:
                sections.append((last_heading, section_content))
            
            last_heading = match.group(2)
            last_end = match.end()
        
        # Get remaining content
        remaining = content[last_end:].strip()
        if remaining:
            sections.append((last_heading, remaining))
        
        # If no sections found, treat whole document as one section
        if not sections:
            sections.append(("Main", content))
        
        return sections
    
    def _split_section(self, content: str) -> Iterator[str]:
        """Split a section into chunks respecting max size."""
        if len(content) <= self.max_chunk_size:
            yield content
            return
        
        # Split by paragraphs first
        paragraphs = re.split(r'\n\n+', content)
        
        current_chunk = ""
        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 <= self.max_chunk_size:
                current_chunk += ("\n\n" + para if current_chunk else para)
            else:
                if current_chunk:
                    yield current_chunk
                
                # If single paragraph is too large, split by sentences
                if len(para) > self.max_chunk_size:
                    yield from self._split_large_paragraph(para)
                    current_chunk = ""
                else:
                    current_chunk = para
        
        if current_chunk:
            yield current_chunk
    
    def _split_large_paragraph(self, para: str) -> Iterator[str]:
        """Split a large paragraph by sentences."""
        sentences = re.split(r'(?<=[.!?])\s+', para)
        
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 <= self.max_chunk_size:
                current_chunk += (" " + sentence if current_chunk else sentence)
            else:
                if current_chunk:
                    yield current_chunk
                current_chunk = sentence
        
        if current_chunk:
            yield current_chunk
    
    def _extract_category(self, file_path: Path) -> str:
        """Extract category from file path."""
        parts = file_path.parts
        # Look for 'tools' in path and get category after it
        if 'tools' in parts:
            idx = parts.index('tools')
            if idx + 1 < len(parts) - 1:  # Has category folder
                return parts[idx + 1]
        if 'general' in parts:
            return 'general'
        return 'unknown'
