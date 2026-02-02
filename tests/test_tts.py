"""
Tests for Text-to-Speech module.
"""

import pytest
import numpy as np
import tempfile
import os


def test_tts_config_defaults():
    """Test TTSConfig has correct defaults."""
    from src.tts import TTSConfig, TTSBackend
    
    config = TTSConfig()
    assert config.backend == TTSBackend.SAPI
    assert config.rate == 0  # SAPI rate: -10 to 10, 0 is normal
    assert config.volume == 100  # SAPI volume: 0 to 100


def test_tts_engine_initialization():
    """Test TextToSpeech can be created."""
    from src.tts import TextToSpeech
    
    tts = TextToSpeech()
    assert not tts.is_loaded


def test_tts_available_backends():
    """Test listing available backends."""
    from src.tts import TextToSpeech
    
    backends = TextToSpeech.list_available_backends()
    assert isinstance(backends, list)
    assert len(backends) > 0
    assert "sapi" in backends


def test_tts_voice_loading():
    """Test loading a voice model."""
    from src.tts import TextToSpeech, TTSBackend
    
    tts = TextToSpeech()
    success = tts.load_voice()
    
    assert success
    assert tts.is_loaded
    assert tts.sample_rate > 0
    assert tts.backend == TTSBackend.SAPI
    
    # Cleanup
    tts.unload_voice()


def test_tts_synthesize():
    """Test synthesizing speech."""
    from src.tts import TextToSpeech
    
    tts = TextToSpeech()
    tts.load_voice()
    
    result = tts.synthesize("Hello, this is a test.")
    
    assert result is not None
    assert result.audio is not None
    assert len(result.audio) > 0
    assert result.sample_rate > 0
    assert result.duration > 0
    assert result.processing_time > 0
    assert result.realtime_factor > 0
    
    # Cleanup
    tts.unload_voice()


def test_tts_synthesize_to_file():
    """Test saving synthesized speech to file."""
    from src.tts import TextToSpeech
    
    tts = TextToSpeech()
    tts.load_voice()
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        output_path = f.name
    
    try:
        duration = tts.synthesize_to_file("Hello, ICL!", output_path)
        
        assert duration > 0
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)
        tts.unload_voice()


def test_tts_list_voices():
    """Test listing available voices."""
    from src.tts import TextToSpeech
    
    tts = TextToSpeech()
    tts.load_voice()
    
    voices = tts.list_voices()
    assert isinstance(voices, list)
    # Windows should have at least one voice
    assert len(voices) > 0
    
    # Each voice should have id and name
    for voice in voices:
        assert 'id' in voice
        assert 'name' in voice
    
    tts.unload_voice()


def test_tts_result_properties():
    """Test TTSResult has correct properties."""
    from src.tts.piper import TTSResult
    
    audio = np.zeros(22050, dtype=np.float32)  # 1 second at 22050Hz
    
    result = TTSResult(
        audio=audio,
        sample_rate=22050,
        duration=1.0,
        processing_time=0.1,
        text="Test"
    )
    
    assert result.realtime_factor == 10.0  # 1.0 / 0.1
