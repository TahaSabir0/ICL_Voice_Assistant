#!/usr/bin/env python3
"""
ICL Knowledge Base Update Script

Master script to update the entire knowledge base:
1. Crawl the ICL website for latest content
2. Download/update PDFs
3. Extract PDF text
4. Regenerate knowledge base markdown files

Usage:
    python scripts/update_knowledge_base.py [--skip-download]
"""

import argparse
import subprocess
import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parent


def run_script(script_name: str, description: str) -> bool:
    """Run a Python script and return success status."""
    script_path = SCRIPTS_DIR / script_name
    
    print(f"\n{'=' * 60}")
    print(f"STEP: {description}")
    print(f"{'=' * 60}")
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=SCRIPTS_DIR.parent,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ ERROR: {script_name} failed with exit code {e.returncode}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Update the ICL knowledge base from the website"
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip crawling and PDF download, only regenerate markdown"
    )
    parser.add_argument(
        "--skip-extract",
        action="store_true",
        help="Skip PDF extraction, only regenerate markdown"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("ICL KNOWLEDGE BASE UPDATE")
    print("=" * 60)
    
    steps = []
    
    if not args.skip_download:
        steps.append(("crawl_icl.py", "Crawling ICL website and downloading PDFs"))
    
    if not args.skip_download and not args.skip_extract:
        steps.append(("extract_pdfs.py", "Extracting text from PDFs"))
    
    steps.append(("generate_knowledge_base.py", "Generating knowledge base markdown files"))
    
    success_count = 0
    for script, description in steps:
        if run_script(script, description):
            success_count += 1
        else:
            print(f"\n⚠️ Stopping due to error in {script}")
            break
    
    print("\n" + "=" * 60)
    print("UPDATE COMPLETE")
    print("=" * 60)
    print(f"Steps completed: {success_count}/{len(steps)}")
    
    if success_count == len(steps):
        print("\n✅ Knowledge base updated successfully!")
        print("\nNext steps:")
        print("  1. Review generated files in knowledge_base/tools/")
        print("  2. Run the ingestion pipeline to update ChromaDB")
        print("     python -m src.rag.ingest")
    else:
        print("\n❌ Update incomplete - check errors above")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
