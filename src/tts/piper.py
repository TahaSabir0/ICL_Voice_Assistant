"""
Text-to-Speech module for ICL Voice Assistant.

Provides a wrapper for local text-to-speech synthesis.
Supports multiple backends:
1. SAPI (Windows built-in) - uses win32com directly, most reliable
2. Piper TTS (neural, high quality) - requires espeak-ng

For production, Piper TTS is recommended but requires:
- espeak-ng to be installed: https://github.com/espeak-ng/espeak-ng/releases
- Set ESPEAK_DATA_PATH environment variable
"""

import numpy as np
import tempfile
import wave
import os
import time
import subprocess
from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path
from enum import Enum


class TTSBackend(Enum):
    """Available TTS backends."""
    SAPI = "sapi"  # Windows SAPI via win32com (most reliable)
    PYTTSX3 = "pyttsx3"  # pyttsx3 wrapper (can have issues)
    PIPER = "piper"  # Piper TTS (requires espeak-ng)


@dataclass
class TTSConfig:
    """Configuration for the TTS engine."""
    # Backend selection
    backend: TTSBackend = TTSBackend.SAPI
    
    # Voice settings
    voice: Optional[str] = None  # Voice name/ID (None = default)
    rate: int = 0  # SAPI rate: -10 to 10, 0 is normal
    volume: int = 100  # Volume 0 to 100
    
    # Piper-specific
    piper_voice: str = "en_US-lessac-medium"
    piper_models_dir: Optional[str] = None


@dataclass
class TTSResult:
    """Result of text-to-speech synthesis."""
    audio: np.ndarray
    sample_rate: int
    duration: float  # Audio duration in seconds
    processing_time: float  # Time taken to synthesize
    text: str  # Original text
    
    @property
    def realtime_factor(self) -> float:
        """How much faster than realtime the synthesis was."""
        return self.duration / self.processing_time if self.processing_time > 0 else 0


class TextToSpeech:
    """
    Text-to-Speech engine with multiple backend support.
    
    Usage:
        tts = TextToSpeech()
        tts.load_voice()
        
        result = tts.synthesize("Hello, welcome to the ICL!")
        # result.audio is a numpy array, result.sample_rate is the sample rate
        
        # Or save directly to file
        tts.synthesize_to_file("Hello!", "output.wav")
    """
    
    def __init__(self, config: Optional[TTSConfig] = None):
        self.config = config or TTSConfig()
        self._engine = None
        self._is_loaded = False
        self._sample_rate = 22050
        self._backend = self.config.backend
    
    @property
    def is_loaded(self) -> bool:
        """Whether the TTS engine is loaded."""
        return self._is_loaded
    
    @property
    def sample_rate(self) -> int:
        """Sample rate of the output audio."""
        return self._sample_rate
    
    @property
    def backend(self) -> TTSBackend:
        """Current backend being used."""
        return self._backend
    
    def load_voice(self, voice_name: Optional[str] = None) -> bool:
        """
        Load a voice model.
        
        Args:
            voice_name: Name of the voice to load. Uses config default if None.
            
        Returns:
            True if loaded successfully.
        """
        voice_name = voice_name or self.config.voice
        
        if self.config.backend == TTSBackend.SAPI:
            return self._load_sapi(voice_name)
        elif self.config.backend == TTSBackend.PYTTSX3:
            return self._load_pyttsx3(voice_name)
        else:
            return self._load_piper(voice_name)
    
    def _load_sapi(self, voice_name: Optional[str]) -> bool:
        """Load Windows SAPI engine via win32com."""
        try:
            import win32com.client
            
            print("Loading Windows SAPI TTS engine...")
            start = time.time()
            
            self._engine = win32com.client.Dispatch("SAPI.SpVoice")
            
            # Set rate and volume
            self._engine.Rate = self.config.rate
            self._engine.Volume = self.config.volume
            
            # Set voice if specified
            if voice_name:
                voices = self._engine.GetVoices()
                for i in range(voices.Count):
                    voice = voices.Item(i)
                    if voice_name.lower() in voice.GetDescription().lower():
                        self._engine.Voice = voice
                        break
            
            # Get voice info
            current_voice = self._engine.Voice.GetDescription()
            
            elapsed = time.time() - start
            print(f"SAPI loaded in {elapsed:.2f}s")
            print(f"Voice: {current_voice}")
            
            self._sample_rate = 22050  # Default for SAPI WAV output
            self._is_loaded = True
            self._backend = TTSBackend.SAPI
            return True
            
        except Exception as e:
            print(f"Failed to load SAPI: {e}")
            print("Falling back to pyttsx3...")
            return self._load_pyttsx3(voice_name)
    
    def _load_pyttsx3(self, voice_name: Optional[str]) -> bool:
        """Load pyttsx3 (Windows SAPI wrapper) engine."""
        try:
            import pyttsx3
            
            print("Loading pyttsx3 TTS engine...")
            start = time.time()
            
            self._engine = pyttsx3.init()
            
            # Set properties - pyttsx3 uses different rate scale (words per minute)
            self._engine.setProperty('rate', 150 + (self.config.rate * 15))
            self._engine.setProperty('volume', self.config.volume / 100.0)
            
            # Set voice if specified
            if voice_name:
                voices = self._engine.getProperty('voices')
                for voice in voices:
                    if voice_name.lower() in voice.name.lower():
                        self._engine.setProperty('voice', voice.id)
                        break
            
            # Get available voices
            voices = self._engine.getProperty('voices')
            
            elapsed = time.time() - start
            print(f"pyttsx3 loaded in {elapsed:.2f}s")
            print(f"Available voices: {len(voices)}")
            
            self._sample_rate = 22050
            self._is_loaded = True
            self._backend = TTSBackend.PYTTSX3
            return True
            
        except Exception as e:
            print(f"Failed to load pyttsx3: {e}")
            return False
    
    def _load_piper(self, voice_name: Optional[str]) -> bool:
        """Load Piper TTS engine. Requires espeak-ng to be installed."""
        try:
            from piper import PiperVoice
            import json
            import urllib.request
            
            voice = voice_name or self.config.piper_voice
            models_dir = Path(self.config.piper_models_dir or Path.home() / ".cache" / "piper_models")
            models_dir.mkdir(parents=True, exist_ok=True)
            
            model_path = models_dir / f"{voice}.onnx"
            config_path = models_dir / f"{voice}.onnx.json"
            
            # Download if needed
            if not model_path.exists():
                print(f"Downloading Piper voice model: {voice}...")
                url = f"https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/{voice}.onnx"
                urllib.request.urlretrieve(url, str(model_path))
            
            if not config_path.exists():
                url = f"https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/{voice}.onnx.json"
                urllib.request.urlretrieve(url, str(config_path))
            
            print(f"Loading Piper voice: {voice}...")
            start = time.time()
            
            self._engine = PiperVoice.load(str(model_path), str(config_path))
            
            # Get sample rate from config
            with open(config_path, encoding='utf-8') as f:
                voice_config = json.load(f)
                self._sample_rate = voice_config.get("audio", {}).get("sample_rate", 22050)
            
            elapsed = time.time() - start
            print(f"Piper loaded in {elapsed:.2f}s (sample rate: {self._sample_rate})")
            
            self._is_loaded = True
            self._backend = TTSBackend.PIPER
            return True
            
        except ImportError as e:
            print(f"Piper not available: {e}")
            print("Falling back to SAPI...")
            return self._load_sapi(voice_name)
        except Exception as e:
            print(f"Failed to load Piper (may need espeak-ng): {e}")
            print("Falling back to SAPI...")
            return self._load_sapi(voice_name)
    
    def synthesize(self, text: str) -> TTSResult:
        """
        Convert text to speech.
        
        Args:
            text: Text to synthesize.
            
        Returns:
            TTSResult with audio data and metadata.
        """
        if not self._is_loaded:
            raise RuntimeError("Voice not loaded. Call load_voice() first.")
        
        start = time.time()
        
        if self._backend == TTSBackend.SAPI:
            audio = self._synthesize_sapi(text)
        elif self._backend == TTSBackend.PYTTSX3:
            audio = self._synthesize_pyttsx3(text)
        else:
            audio = self._synthesize_piper(text)
        
        processing_time = time.time() - start
        duration = len(audio) / self._sample_rate
        
        return TTSResult(
            audio=audio,
            sample_rate=self._sample_rate,
            duration=duration,
            processing_time=processing_time,
            text=text
        )
    
    def _synthesize_sapi(self, text: str) -> np.ndarray:
        """Synthesize using Windows SAPI directly via win32com."""
        import win32com.client
        
        # Create temp file for output
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            output_path = f.name
        
        try:
            # Create a new SpVoice for each synthesis to avoid state issues
            voice = win32com.client.Dispatch("SAPI.SpVoice")
            voice.Rate = self.config.rate
            voice.Volume = self.config.volume
            
            # If we have an engine with a specific voice set, copy it
            if self._engine and hasattr(self._engine, 'Voice'):
                voice.Voice = self._engine.Voice
            
            # Create file stream for output
            stream = win32com.client.Dispatch("SAPI.SpFileStream")
            stream.Open(output_path, 3)  # 3 = SSFMCreateForWrite
            
            voice.AudioOutputStream = stream
            voice.Speak(text)
            
            stream.Close()
            
            # Read the WAV file
            with wave.open(output_path, 'rb') as wav_file:
                self._sample_rate = wav_file.getframerate()
                n_channels = wav_file.getnchannels()
                frames = wav_file.readframes(wav_file.getnframes())
                audio = np.frombuffer(frames, dtype=np.int16)
                
                # Convert stereo to mono if needed
                if n_channels == 2:
                    audio = audio.reshape(-1, 2).mean(axis=1).astype(np.int16)
            
            # Convert to float32
            audio = audio.astype(np.float32) / 32768.0
            
            return audio
            
        finally:
            # Cleanup temp file
            if os.path.exists(output_path):
                try:
                    os.unlink(output_path)
                except Exception:
                    pass
    
    def _synthesize_pyttsx3(self, text: str) -> np.ndarray:
        """Synthesize using pyttsx3 (saves to temp file, then loads)."""
        import pyttsx3
        
        # Create temp file for output
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            output_path = f.name
        
        try:
            # Create a fresh engine for each call to avoid pyttsx3 getting stuck
            engine = pyttsx3.init()
            engine.setProperty('rate', 150 + (self.config.rate * 15))
            engine.setProperty('volume', self.config.volume / 100.0)
            
            # Synthesize to file
            engine.save_to_file(text, output_path)
            engine.runAndWait()
            engine.stop()
            
            # Read back as numpy array
            with wave.open(output_path, 'rb') as wav_file:
                self._sample_rate = wav_file.getframerate()
                n_channels = wav_file.getnchannels()
                frames = wav_file.readframes(wav_file.getnframes())
                audio = np.frombuffer(frames, dtype=np.int16)
                
                # Convert stereo to mono if needed
                if n_channels == 2:
                    audio = audio.reshape(-1, 2).mean(axis=1).astype(np.int16)
            
            # Convert to float32
            audio = audio.astype(np.float32) / 32768.0
            
            return audio
            
        finally:
            # Cleanup temp file
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def _synthesize_piper(self, text: str) -> np.ndarray:
        """Synthesize using Piper TTS."""
        # Piper synthesize returns an iterable of AudioChunk objects
        audio_chunks = []
        
        for audio_chunk in self._engine.synthesize(text):
            audio_chunks.append(audio_chunk.audio_bytes)
        
        # Combine all chunks
        all_audio_bytes = b''.join(audio_chunks)
        
        # Convert to numpy array
        audio = np.frombuffer(all_audio_bytes, dtype=np.int16)
        
        # Convert to float32
        audio = audio.astype(np.float32) / 32768.0
        
        return audio
    
    def synthesize_to_file(self, text: str, output_path: str) -> float:
        """
        Synthesize text and save to WAV file.
        
        Args:
            text: Text to synthesize.
            output_path: Path to save WAV file.
            
        Returns:
            Duration of the audio in seconds.
        """
        result = self.synthesize(text)
        
        # Convert back to int16 for WAV
        audio_int16 = (result.audio * 32768).astype(np.int16)
        
        with wave.open(output_path, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(result.sample_rate)
            wav_file.writeframes(audio_int16.tobytes())
        
        return result.duration
    
    def unload_voice(self):
        """Unload the voice to free memory."""
        self._engine = None
        self._is_loaded = False
    
    def list_voices(self) -> List[dict]:
        """List available voices for the current backend."""
        if self._backend == TTSBackend.SAPI and self._engine:
            voices = self._engine.GetVoices()
            return [{'id': str(i), 'name': voices.Item(i).GetDescription()} 
                    for i in range(voices.Count)]
        elif self._backend == TTSBackend.PYTTSX3 and self._engine:
            voices = self._engine.getProperty('voices')
            return [{'id': v.id, 'name': v.name} for v in voices]
        return []
    
    @staticmethod
    def list_available_backends() -> List[str]:
        """List available TTS backends."""
        return [b.value for b in TTSBackend]


def create_tts_engine(
    backend: str = "sapi",
    load_immediately: bool = True
) -> TextToSpeech:
    """
    Factory function to create and optionally load a TTS engine.
    
    Args:
        backend: Backend to use ("sapi", "pyttsx3", or "piper").
        load_immediately: Whether to load the voice immediately.
        
    Returns:
        Configured TextToSpeech instance.
    """
    backend_map = {
        "sapi": TTSBackend.SAPI,
        "pyttsx3": TTSBackend.PYTTSX3,
        "piper": TTSBackend.PIPER,
    }
    backend_enum = backend_map.get(backend, TTSBackend.SAPI)
    config = TTSConfig(backend=backend_enum)
    tts = TextToSpeech(config)
    
    if load_immediately:
        tts.load_voice()
    
    return tts
