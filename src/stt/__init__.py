"""
Speech-to-text module using Faster Whisper.

This module provides:
- SpeechToText: Main STT engine class
- TranscriptionResult: Result object with text and metadata
- create_stt_engine: Factory function for easy setup
"""

from .whisper import (
    SpeechToText,
    STTConfig,
    TranscriptionResult,
    WhisperModelSize,
    create_stt_engine,
)

__all__ = [
    "SpeechToText",
    "STTConfig",
    "TranscriptionResult",
    "WhisperModelSize",
    "create_stt_engine",
]
