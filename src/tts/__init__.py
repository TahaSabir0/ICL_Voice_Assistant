"""
Text-to-speech module for ICL Voice Assistant.

This module provides:
- TextToSpeech: Main TTS engine class with multiple backend support
- TTSResult: Result object with audio and metadata
- create_tts_engine: Factory function for easy setup

Backends:
- sapi: Windows SAPI via win32com (most reliable)
- pyttsx3: pyttsx3 wrapper (can have issues with multiple calls)
- piper: Piper TTS (requires espeak-ng, higher quality)
"""

from .piper import (
    TextToSpeech,
    TTSConfig,
    TTSResult,
    TTSBackend,
    create_tts_engine,
)

__all__ = [
    "TextToSpeech",
    "TTSConfig",
    "TTSResult",
    "TTSBackend",
    "create_tts_engine",
]
