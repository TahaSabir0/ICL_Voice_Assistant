"""
Kiosk UI module using PySide6.

This module provides the full-screen kiosk interface for the ICL Voice Assistant.
"""

from .kiosk_window import KioskWindow, launch_kiosk
from .kiosk_app import KioskApplication, main as run_kiosk
from .pipeline_worker import PipelineWorker, PipelineThread
from .widgets import (
    PushToTalkButton,
    StateIndicator,
    PulsingDots,
    ConversationView,
    MessageBubble,
)
from .styles import COLORS, FONTS, MAIN_STYLESHEET

__all__ = [
    # Main application
    "KioskApplication",
    "run_kiosk",
    # Main window
    "KioskWindow",
    "launch_kiosk",
    # Pipeline integration
    "PipelineWorker",
    "PipelineThread",
    # Widgets
    "PushToTalkButton",
    "StateIndicator",
    "PulsingDots",
    "ConversationView",
    "MessageBubble",
    # Styles
    "COLORS",
    "FONTS",
    "MAIN_STYLESHEET",
]

