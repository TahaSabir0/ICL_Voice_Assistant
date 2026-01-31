"""
Audio capture and playback modules.

This module provides:
- AudioCapture: Record from microphone with silence detection
- AudioPlayback: Play audio through speakers
"""

from .capture import (
    AudioCapture,
    AudioConfig,
    RecordingState,
    list_audio_devices,
    get_default_input_device,
)

from .playback import (
    AudioPlayback,
    PlaybackState,
    play_audio,
    get_default_output_device,
)

__all__ = [
    # Capture
    "AudioCapture",
    "AudioConfig", 
    "RecordingState",
    "list_audio_devices",
    "get_default_input_device",
    # Playback
    "AudioPlayback",
    "PlaybackState",
    "play_audio",
    "get_default_output_device",
]
