"""
Audio playback module for ICL Voice Assistant.

Handles playing audio through the speakers.
"""

import numpy as np
import sounddevice as sd
import threading
from typing import Optional, Callable
from enum import Enum


class PlaybackState(Enum):
    """States for the audio player."""
    IDLE = "idle"
    PLAYING = "playing"
    STOPPED = "stopped"


class AudioPlayback:
    """
    Plays audio through the system speakers.
    
    Usage:
        player = AudioPlayback()
        
        # Play audio (blocking)
        player.play(audio_data, sample_rate=22050)
        
        # Or play non-blocking
        player.play_async(audio_data, sample_rate=22050)
        player.wait()  # Wait for completion
    """
    
    def __init__(self):
        self._state = PlaybackState.IDLE
        self._playback_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._on_state_change: Optional[Callable[[PlaybackState], None]] = None
        self._on_complete: Optional[Callable[[], None]] = None
    
    @property
    def state(self) -> PlaybackState:
        """Current playback state."""
        return self._state
    
    @property
    def is_playing(self) -> bool:
        """Whether currently playing."""
        return self._state == PlaybackState.PLAYING
    
    def set_callbacks(
        self,
        on_state_change: Optional[Callable[[PlaybackState], None]] = None,
        on_complete: Optional[Callable[[], None]] = None
    ):
        """Set callback functions."""
        self._on_state_change = on_state_change
        self._on_complete = on_complete
    
    def _set_state(self, state: PlaybackState):
        """Update state and notify callback."""
        self._state = state
        if self._on_state_change:
            self._on_state_change(state)
    
    def play(
        self,
        audio: np.ndarray,
        sample_rate: int = 22050,
        blocking: bool = True
    ) -> bool:
        """
        Play audio through speakers.
        
        Args:
            audio: Audio data as numpy array (float32 or int16).
            sample_rate: Sample rate of the audio.
            blocking: If True, wait for playback to complete.
            
        Returns:
            True if playback started successfully.
        """
        if self._state == PlaybackState.PLAYING:
            return False
        
        self._stop_event.clear()
        
        # Ensure audio is the right format
        if audio.dtype != np.float32:
            if audio.dtype == np.int16:
                audio = audio.astype(np.float32) / 32768.0
            else:
                audio = audio.astype(np.float32)
        
        # Ensure 1D or 2D array
        if audio.ndim == 1:
            audio = audio.reshape(-1, 1)
        
        try:
            self._set_state(PlaybackState.PLAYING)
            
            if blocking:
                sd.play(audio, samplerate=sample_rate)
                sd.wait()
                self._set_state(PlaybackState.STOPPED)
                if self._on_complete:
                    self._on_complete()
            else:
                # Non-blocking playback in separate thread
                def _play_thread():
                    try:
                        sd.play(audio, samplerate=sample_rate)
                        sd.wait()
                    finally:
                        self._set_state(PlaybackState.STOPPED)
                        if self._on_complete:
                            self._on_complete()
                
                self._playback_thread = threading.Thread(target=_play_thread)
                self._playback_thread.start()
            
            return True
            
        except Exception as e:
            print(f"Playback error: {e}")
            self._set_state(PlaybackState.IDLE)
            return False
    
    def play_async(self, audio: np.ndarray, sample_rate: int = 22050) -> bool:
        """Play audio asynchronously (non-blocking)."""
        return self.play(audio, sample_rate, blocking=False)
    
    def stop(self):
        """Stop current playback."""
        sd.stop()
        self._stop_event.set()
        self._set_state(PlaybackState.STOPPED)
    
    def wait(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for playback to complete.
        
        Args:
            timeout: Maximum time to wait in seconds.
            
        Returns:
            True if playback completed, False if timeout.
        """
        if self._playback_thread:
            self._playback_thread.join(timeout=timeout)
            return not self._playback_thread.is_alive()
        return True


def play_audio(audio: np.ndarray, sample_rate: int = 22050):
    """
    Simple function to play audio (blocking).
    
    Args:
        audio: Audio data as numpy array.
        sample_rate: Sample rate of the audio.
    """
    player = AudioPlayback()
    player.play(audio, sample_rate, blocking=True)


def get_default_output_device():
    """Get information about the default output device."""
    try:
        device = sd.query_devices(kind='output')
        return {
            'name': device['name'],
            'channels': device['max_output_channels'],
            'sample_rate': device['default_samplerate']
        }
    except Exception:
        return None
