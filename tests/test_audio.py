"""
Tests for audio capture module.
"""

import pytest
import numpy as np
import time


def test_audio_config_defaults():
    """Test AudioConfig has correct defaults."""
    from src.audio import AudioConfig
    
    config = AudioConfig()
    assert config.sample_rate == 16000
    assert config.channels == 1
    assert config.silence_threshold == 0.01
    assert config.silence_duration == 1.5
    assert config.max_duration == 30.0


def test_audio_capture_initialization():
    """Test AudioCapture can be created."""
    from src.audio import AudioCapture, RecordingState
    
    capture = AudioCapture()
    assert capture.state == RecordingState.IDLE
    assert not capture.is_recording


def test_list_audio_devices():
    """Test listing audio devices."""
    from src.audio import list_audio_devices, get_default_input_device
    
    devices = list_audio_devices()
    assert isinstance(devices, list)
    
    # Should have at least one input device
    assert len(devices) > 0, "No audio input devices found"
    
    # Each device should have required fields
    for device in devices:
        assert 'name' in device
        assert 'channels' in device
    
    # Default device should exist
    default = get_default_input_device()
    assert default is not None
    assert 'name' in default


def test_audio_playback_initialization():
    """Test AudioPlayback can be created."""
    from src.audio import AudioPlayback, PlaybackState
    
    player = AudioPlayback()
    assert player.state == PlaybackState.IDLE
    assert not player.is_playing


def test_audio_playback_with_sine_wave():
    """Test playing a simple sine wave."""
    from src.audio import AudioPlayback
    
    # Generate a short sine wave (0.1 seconds)
    sample_rate = 22050
    duration = 0.1
    frequency = 440  # A4 note
    
    t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
    audio = 0.3 * np.sin(2 * np.pi * frequency * t)
    
    player = AudioPlayback()
    success = player.play(audio, sample_rate=sample_rate, blocking=True)
    
    assert success
    # After blocking play, state should be stopped
    from src.audio import PlaybackState
    assert player.state == PlaybackState.STOPPED


def test_audio_capture_start_stop():
    """Test starting and stopping recording."""
    from src.audio import AudioCapture, RecordingState
    
    capture = AudioCapture()
    
    # Start recording
    success = capture.start()
    assert success
    assert capture.state == RecordingState.RECORDING
    
    # Wait a tiny bit
    time.sleep(0.2)
    
    # Stop recording
    capture.stop()
    
    # Should have captured some audio
    audio = capture.get_audio()
    assert audio is not None
    assert len(audio) > 0
