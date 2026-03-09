#!/usr/bin/env python3
"""
Launch script for the ICL Voice Assistant Kiosk.

Usage:
    python scripts/launch_kiosk.py            # Fullscreen kiosk mode
    python scripts/launch_kiosk.py --windowed # Windowed mode for testing
    python scripts/launch_kiosk.py --no-rag   # Disable RAG (basic LLM only)
"""

import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()  # Required for multiprocessing on Windows
    
    # Fix sentence-transformers / tokenizer parallelism issues in spawned processes
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    
    # Import GUI only in the main process, NOT in spawned subprocesses
    from src.ui.kiosk_app import main
    sys.exit(main())
