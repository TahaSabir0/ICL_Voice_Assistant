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

from src.ui.kiosk_app import main

if __name__ == "__main__":
    sys.exit(main())
