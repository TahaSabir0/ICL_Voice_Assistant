"""
ICL Voice Assistant - Local AI voice assistant for the Innovation & Creativity Lab.

Components:
- audio: Microphone capture and speaker playback
- stt: Speech-to-text using Faster Whisper
- llm: LLM client using Ollama
- tts: Text-to-speech with multiple backends
- pipeline: Main voice pipeline orchestration
"""

__version__ = "0.1.0"

from .pipeline import (
    VoicePipeline,
    PipelineConfig,
    PipelineState,
    PipelineMetrics,
    ConversationTurn,
    create_pipeline,
)

__all__ = [
    "__version__",
    "VoicePipeline",
    "PipelineConfig",
    "PipelineState",
    "PipelineMetrics",
    "ConversationTurn",
    "create_pipeline",
]
