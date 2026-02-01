#!/usr/bin/env python3
"""
PDF Text Extractor

Extracts text from all downloaded PDFs and saves as text files.
Uses PyMuPDF (fitz) for reliable text extraction.

Usage:
    python scripts/extract_pdfs.py
"""

import json
import re
from pathlib import Path

import fitz  # PyMuPDF


# Configuration
OUTPUT_DIR = Path(__file__).parent.parent / "knowledge_base"
PDF_DIR = OUTPUT_DIR / "pdfs"
RAW_DIR = OUTPUT_DIR / "raw"
EXTRACTED_DIR = RAW_DIR / "pdf_text"


def clean_extracted_text(text: str) -> str:
    """Clean up extracted PDF text."""
    # Remove excessive whitespace
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    # Remove trailing spaces
    text = re.sub(r' +\n', '\n', text)
    # Remove leading spaces on lines (but preserve indentation for lists)
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        # Keep reasonable indentation (up to 8 spaces) but remove excessive
        if line.startswith('        '):
            line = '    ' + line.strip()
        cleaned_lines.append(line.rstrip())
    
    return '\n'.join(cleaned_lines).strip()


def extract_pdf_text(pdf_path: Path) -> dict:
    """Extract text from a PDF file."""
    print(f"  Extracting: {pdf_path.name}")
    
    result = {
        "file": pdf_path.name,
        "pages": 0,
        "text": "",
        "error": None
    }
    
    try:
        doc = fitz.open(pdf_path)
        result["pages"] = len(doc)
        
        all_text = []
        for page_num, page in enumerate(doc, 1):
            page_text = page.get_text()
            if page_text.strip():
                all_text.append(f"--- Page {page_num} ---\n{page_text}")
        
        doc.close()
        
        full_text = '\n\n'.join(all_text)
        result["text"] = clean_extracted_text(full_text)
        
        print(f"    ✓ {result['pages']} pages, {len(result['text']):,} chars")
        
    except Exception as e:
        result["error"] = str(e)
        print(f"    ✗ Error: {e}")
    
    return result


def categorize_pdf(filename: str) -> str:
    """Categorize a PDF based on its filename."""
    filename_lower = filename.lower()
    
    if any(x in filename_lower for x in ['3d', 'ender', 'elegoo', 'creality', 'ld-002', 'saturn', 'pla', 'petg', 'resin']):
        return "3d_printing"
    elif any(x in filename_lower for x in ['laser', 'mf1624']):
        return "laser_cutting"
    elif any(x in filename_lower for x in ['cnc', 'carve']):
        return "cnc_machining"
    elif any(x in filename_lower for x in ['sewing', 'embroidery', 'janome', 'serger']):
        return "sewing_embroidery"
    elif any(x in filename_lower for x in ['vr', 'virtual', 'oculus', 'quest', 'vive', 'go.pdf']):
        return "virtual_reality"
    elif any(x in filename_lower for x in ['vinyl', 'heat', 'titan', 'dogechee', 'vevor']):
        return "vinyl_cutting"
    else:
        return "general"


def main():
    """Main extraction function."""
    print("=" * 60)
    print("PDF Text Extractor")
    print("=" * 60)
    
    # Ensure output directory exists
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get all PDFs
    pdf_files = list(PDF_DIR.glob("*.pdf"))
    print(f"\nFound {len(pdf_files)} PDFs to process\n")
    
    # Extract text from each PDF
    extractions = []
    categories = {}
    
    for pdf_path in sorted(pdf_files):
        result = extract_pdf_text(pdf_path)
        result["category"] = categorize_pdf(pdf_path.name)
        extractions.append(result)
        
        # Track by category
        cat = result["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(result)
        
        # Save individual text file
        if result["text"]:
            txt_filename = pdf_path.stem + ".txt"
            txt_path = EXTRACTED_DIR / txt_filename
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"# {pdf_path.stem}\n\n")
                f.write(f"Source: {pdf_path.name}\n")
                f.write(f"Category: {result['category']}\n")
                f.write(f"Pages: {result['pages']}\n")
                f.write("=" * 40 + "\n\n")
                f.write(result["text"])
    
    # Save extraction summary
    summary = {
        "total_pdfs": len(pdf_files),
        "successful": sum(1 for e in extractions if not e["error"]),
        "failed": sum(1 for e in extractions if e["error"]),
        "by_category": {cat: len(items) for cat, items in categories.items()},
        "extractions": [
            {
                "file": e["file"],
                "category": e["category"],
                "pages": e["pages"],
                "chars": len(e["text"]),
                "error": e["error"]
            }
            for e in extractions
        ]
    }
    
    summary_path = RAW_DIR / "pdf_extraction_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE")
    print("=" * 60)
    print(f"Total PDFs: {summary['total_pdfs']}")
    print(f"Successful: {summary['successful']}")
    print(f"Failed: {summary['failed']}")
    print(f"\nBy category:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count} PDFs")
    print(f"\nOutput: {EXTRACTED_DIR}")
    
    return extractions


if __name__ == "__main__":
    main()
