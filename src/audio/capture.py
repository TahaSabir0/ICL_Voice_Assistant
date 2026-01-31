"""
Audio capture module for ICL Voice Assistant.

Handles recording from the microphone with silence detection
to automatically stop when the user finishes speaking.
"""

import numpy as np
import sounddevice as sd
import threading
import queue
import time
from dataclasses import dataclass
from typing import Optional, Callable
from enum import Enum


class RecordingState(Enum):
    """States for the audio recorder."""
    IDLE = "idle"
    RECORDING = "recording"
    STOPPED = "stopped"


@dataclass
class AudioConfig:
    """Configuration for audio capture."""
    sample_rate: int = 16000  # 16kHz for Whisper compatibility
    channels: int = 1  # Mono
    dtype: np.dtype = np.float32
    blocksize: int = 1024  # Samples per block
    
    # Silence detection
    silence_threshold: float = 0.01  # RMS threshold for silence
    silence_duration: float = 1.5  # Seconds of silence to stop recording
    max_duration: float = 30.0  # Maximum recording duration in seconds
    min_duration: float = 0.5  # Minimum recording duration


class AudioCapture:
    """
    Captures audio from the microphone with automatic silence detection.
    
    Usage:
        capture = AudioCapture()
        
        # Start recording (non-blocking)
        capture.start()
        
        # ... wait for user to finish speaking ...
        
        # Get the recorded audio
        audio = capture.get_audio()
        
        # Or stop manually
        capture.stop()
    """
    
    def __init__(self, config: Optional[AudioConfig] = None):
        self.config = config or AudioConfig()
        self._state = RecordingState.IDLE
        self._audio_queue: queue.Queue = queue.Queue()
        self._audio_buffer: list = []
        self._stream: Optional[sd.InputStream] = None
        self._recording_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Callbacks
        self._on_state_change: Optional[Callable[[RecordingState], None]] = None
        self._on_audio_level: Optional[Callable[[float], None]] = None
    
    @property
    def state(self) -> RecordingState:
        """Current recording state."""
        return self._state
    
    @property
    def is_recording(self) -> bool:
        """Whether currently recording."""
        return self._state == RecordingState.RECORDING
    
    def set_callbacks(
        self,
        on_state_change: Optional[Callable[[RecordingState], None]] = None,
        on_audio_level: Optional[Callable[[float], None]] = None
    ):
        """Set callback functions for state changes and audio levels."""
        self._on_state_change = on_state_change
        self._on_audio_level = on_audio_level
    
    def _set_state(self, state: RecordingState):
        """Update state and notify callback."""
        self._state = state
        if self._on_state_change:
            self._on_state_change(state)
    
    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status):
        """Callback for sounddevice stream - receives audio chunks."""
        if status:
            print(f"Audio callback status: {status}")
        
        # Put audio data in queue for processing
        self._audio_queue.put(indata.copy())
    
    def _calculate_rms(self, audio: np.ndarray) -> float:
        """Calculate RMS (volume level) of audio chunk."""
        return float(np.sqrt(np.mean(audio ** 2)))
    
    def _recording_loop(self):
        """Main recording loop with silence detection."""
        silence_samples = 0
        samples_for_silence = int(
            self.config.silence_duration * self.config.sample_rate / self.config.blocksize
        )
        total_samples = 0
        max_samples = int(
            self.config.max_duration * self.config.sample_rate / self.config.blocksize
        )
        min_samples = int(
            self.config.min_duration * self.config.sample_rate / self.config.blocksize
        )
        
        has_speech = False
        
        while not self._stop_event.is_set():
            try:
                # Get audio chunk from queue (with timeout)
                audio_chunk = self._audio_queue.get(timeout=0.1)
                self._audio_buffer.append(audio_chunk)
                total_samples += 1
                
                # Calculate audio level
                rms = self._calculate_rms(audio_chunk)
                if self._on_audio_level:
                    self._on_audio_level(rms)
                
                # Check for silence
                if rms < self.config.silence_threshold:
                    silence_samples += 1
                else:
                    silence_samples = 0
                    has_speech = True
                
                # Stop conditions
                if total_samples >= max_samples:
                    # Max duration reached
                    break
                
                if has_speech and total_samples >= min_samples:
                    if silence_samples >= samples_for_silence:
                        # Detected silence after speech
                        break
                
            except queue.Empty:
                continue
        
        # Stop the stream
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        
        self._set_state(RecordingState.STOPPED)
    
    def start(self) -> bool:
        """
        Start recording audio.
        
        Returns:
            True if recording started successfully, False otherwise.
        """
        if self._state == RecordingState.RECORDING:
            return False
        
        # Reset state
        self._audio_buffer = []
        self._audio_queue = queue.Queue()
        self._stop_event.clear()
        
        try:
            # Create and start the audio stream
            self._stream = sd.InputStream(
                samplerate=self.config.sample_rate,
                channels=self.config.channels,
                dtype=self.config.dtype,
                blocksize=self.config.blocksize,
                callback=self._audio_callback
            )
            self._stream.start()
            
            # Start the recording loop in a separate thread
            self._recording_thread = threading.Thread(target=self._recording_loop)
            self._recording_thread.start()
            
            self._set_state(RecordingState.RECORDING)
            return True
            
        except Exception as e:
            print(f"Failed to start recording: {e}")
            return False
    
    def stop(self):
        """Stop recording manually."""
        self._stop_event.set()
        
        if self._recording_thread:
            self._recording_thread.join(timeout=2.0)
            self._recording_thread = None
    
    def get_audio(self) -> Optional[np.ndarray]:
        """
        Get the recorded audio as a numpy array.
        
        Returns:
            Audio data as float32 numpy array, or None if no audio recorded.
        """
        if not self._audio_buffer:
            return None
        
        # Concatenate all audio chunks
        audio = np.concatenate(self._audio_buffer, axis=0)
        
        # Flatten to 1D if needed
        if audio.ndim > 1:
            audio = audio.flatten()
        
        return audio
    
    def get_audio_duration(self) -> float:
        """Get the duration of recorded audio in seconds."""
        audio = self.get_audio()
        if audio is None:
            return 0.0
        return len(audio) / self.config.sample_rate
    
    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for recording to complete.
        
        Args:
            timeout: Maximum time to wait in seconds.
            
        Returns:
            True if recording completed, False if timeout.
        """
        if self._recording_thread:
            self._recording_thread.join(timeout=timeout)
            return not self._recording_thread.is_alive()
        return True


def list_audio_devices():
    """List available audio input devices."""
    devices = sd.query_devices()
    input_devices = []
    
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            input_devices.append({
                'index': i,
                'name': device['name'],
                'channels': device['max_input_channels'],
                'sample_rate': device['default_samplerate']
            })
    
    return input_devices


def get_default_input_device():
    """Get information about the default input device."""
    try:
        device = sd.query_devices(kind='input')
        return {
            'name': device['name'],
            'channels': device['max_input_channels'],
            'sample_rate': device['default_samplerate']
        }
    except Exception as e:
        return None
