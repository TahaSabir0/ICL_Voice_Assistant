"""
Tests for Speech-to-Text module.
"""

import pytest
import numpy as np
import time


def test_stt_config_defaults():
    """Test STTConfig has correct defaults."""
    from src.stt import STTConfig
    
    config = STTConfig()
    assert config.model_size == "base"
    assert config.beam_size == 5
    assert config.vad_filter == True


def test_stt_engine_initialization():
    """Test SpeechToText can be created."""
    from src.stt import SpeechToText, STTConfig
    
    stt = SpeechToText()
    assert not stt.is_loaded


def test_stt_model_loading():
    """Test loading the Whisper model."""
    from src.stt import SpeechToText, STTConfig
    
    # Use tiny model for faster testing
    config = STTConfig(model_size="tiny", device="cpu", compute_type="int8")
    stt = SpeechToText(config)
    
    success = stt.load_model()
    assert success
    assert stt.is_loaded
    
    # Cleanup
    stt.unload_model()
    assert not stt.is_loaded


def test_stt_transcribe_silence():
    """Test transcribing near-silent audio."""
    from src.stt import SpeechToText, STTConfig
    
    # Use tiny model for faster testing
    config = STTConfig(model_size="tiny", device="cpu", compute_type="int8")
    stt = SpeechToText(config)
    stt.load_model()
    
    # Create silent audio (2 seconds at 16kHz)
    silent_audio = np.zeros(32000, dtype=np.float32)
    
    # Add tiny noise to avoid completely empty
    silent_audio += np.random.randn(32000).astype(np.float32) * 0.001
    
    result = stt.transcribe(silent_audio)
    
    # Should complete without error
    assert result is not None
    assert result.duration > 0
    
    # Cleanup
    stt.unload_model()


def test_stt_transcribe_tone():
    """Test transcribing audio with a tone (no speech)."""
    from src.stt import SpeechToText, STTConfig
    
    # Use tiny model for faster testing
    config = STTConfig(model_size="tiny", device="cpu", compute_type="int8")
    stt = SpeechToText(config)
    stt.load_model()
    
    # Create a 440Hz tone (1 second at 16kHz)
    sample_rate = 16000
    t = np.linspace(0, 1, sample_rate, dtype=np.float32)
    tone_audio = 0.5 * np.sin(2 * np.pi * 440 * t)
    
    result = stt.transcribe(tone_audio)
    
    # Should complete without error
    assert result is not None
    assert result.duration > 0
    
    # Cleanup
    stt.unload_model()


def test_transcription_result_properties():
    """Test TranscriptionResult has correct properties."""
    from src.stt.whisper import TranscriptionResult
    
    result = TranscriptionResult(
        text="Hello world",
        language="en",
        language_probability=0.99,
        duration=1.0,
        processing_time=0.5,
        segments=[]
    )
    
    assert result.text == "Hello world"
    assert result.language == "en"
    assert result.words_per_second == 4.0  # 2 words / 0.5 seconds
