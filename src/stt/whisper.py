"""
Speech-to-Text module using Faster Whisper.

Provides a wrapper around Faster Whisper for transcribing audio to text.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, List, Tuple
from enum import Enum
import time


class WhisperModelSize(Enum):
    """Available Whisper model sizes."""
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large-v3"


@dataclass
class TranscriptionResult:
    """Result of a transcription."""
    text: str
    language: str
    language_probability: float
    duration: float  # Audio duration in seconds
    processing_time: float  # Time taken to transcribe
    segments: List[dict]  # Individual segments with timestamps
    
    @property
    def words_per_second(self) -> float:
        """Processing speed in words per second."""
        word_count = len(self.text.split())
        return word_count / self.processing_time if self.processing_time > 0 else 0


@dataclass
class STTConfig:
    """Configuration for the STT engine."""
    model_size: str = "base"  # tiny, base, small, medium, large-v3
    device: str = "cuda"  # cuda, cpu, auto
    compute_type: str = "float16"  # float16, int8, int8_float16
    language: Optional[str] = None  # None for auto-detect, "en" for English
    beam_size: int = 5
    vad_filter: bool = True  # Voice Activity Detection filter
    vad_parameters: Optional[dict] = None


class SpeechToText:
    """
    Speech-to-Text engine using Faster Whisper.
    
    Usage:
        stt = SpeechToText()
        stt.load_model()  # Load model (can take a few seconds)
        
        result = stt.transcribe(audio_data)
        print(result.text)
    """
    
    def __init__(self, config: Optional[STTConfig] = None):
        self.config = config or STTConfig()
        self._model = None
        self._is_loaded = False
    
    @property
    def is_loaded(self) -> bool:
        """Whether the model is loaded."""
        return self._is_loaded
    
    def load_model(self) -> bool:
        """
        Load the Whisper model.
        
        Returns:
            True if loaded successfully.
        """
        try:
            from faster_whisper import WhisperModel
            
            # Determine device
            device = self.config.device
            compute_type = self.config.compute_type
            
            if device == "auto":
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # Adjust compute type for CPU
            if device == "cpu" and compute_type == "float16":
                compute_type = "int8"
            
            print(f"Loading Whisper model '{self.config.model_size}' on {device}...")
            start = time.time()
            
            self._model = WhisperModel(
                self.config.model_size,
                device=device,
                compute_type=compute_type
            )
            
            elapsed = time.time() - start
            print(f"Model loaded in {elapsed:.2f}s")
            
            self._is_loaded = True
            return True
            
        except Exception as e:
            print(f"Failed to load Whisper model: {e}")
            return False
    
    def unload_model(self):
        """Unload the model to free memory."""
        if self._model:
            del self._model
            self._model = None
            self._is_loaded = False
            
            # Force garbage collection
            import gc
            gc.collect()
            
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass
    
    def transcribe(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000
    ) -> TranscriptionResult:
        """
        Transcribe audio to text.
        
        Args:
            audio: Audio data as float32 numpy array.
            sample_rate: Sample rate of the audio (should be 16000 for Whisper).
            
        Returns:
            TranscriptionResult with text and metadata.
        """
        if not self._is_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        # Ensure audio is float32 and 1D
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
        if audio.ndim > 1:
            audio = audio.flatten()
        
        # Resample if needed (Whisper expects 16kHz)
        if sample_rate != 16000:
            # Simple resampling (for production, use librosa or scipy)
            from scipy import signal
            num_samples = int(len(audio) * 16000 / sample_rate)
            audio = signal.resample(audio, num_samples)
            sample_rate = 16000
        
        # Calculate audio duration
        audio_duration = len(audio) / sample_rate
        
        # Prepare VAD parameters
        vad_params = self.config.vad_parameters or {
            "min_silence_duration_ms": 500,
            "speech_pad_ms": 200
        }
        
        # Transcribe
        start = time.time()
        
        segments, info = self._model.transcribe(
            audio,
            language=self.config.language,
            beam_size=self.config.beam_size,
            vad_filter=self.config.vad_filter,
            vad_parameters=vad_params if self.config.vad_filter else None
        )
        
        # Collect segments
        segment_list = []
        text_parts = []
        
        for segment in segments:
            segment_list.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            })
            text_parts.append(segment.text.strip())
        
        processing_time = time.time() - start
        
        # Join all text
        full_text = " ".join(text_parts)
        
        return TranscriptionResult(
            text=full_text,
            language=info.language,
            language_probability=info.language_probability,
            duration=audio_duration,
            processing_time=processing_time,
            segments=segment_list
        )
    
    def transcribe_file(self, audio_path: str) -> TranscriptionResult:
        """
        Transcribe audio from a file.
        
        Args:
            audio_path: Path to the audio file.
            
        Returns:
            TranscriptionResult with text and metadata.
        """
        if not self._is_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        start = time.time()
        
        segments, info = self._model.transcribe(
            audio_path,
            language=self.config.language,
            beam_size=self.config.beam_size,
            vad_filter=self.config.vad_filter
        )
        
        # Collect segments
        segment_list = []
        text_parts = []
        
        for segment in segments:
            segment_list.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            })
            text_parts.append(segment.text.strip())
        
        processing_time = time.time() - start
        full_text = " ".join(text_parts)
        
        # Estimate duration from last segment
        audio_duration = segment_list[-1]["end"] if segment_list else 0
        
        return TranscriptionResult(
            text=full_text,
            language=info.language,
            language_probability=info.language_probability,
            duration=audio_duration,
            processing_time=processing_time,
            segments=segment_list
        )


def create_stt_engine(
    model_size: str = "base",
    device: str = "auto",
    load_immediately: bool = True
) -> SpeechToText:
    """
    Factory function to create and optionally load an STT engine.
    
    Args:
        model_size: Whisper model size (tiny, base, small, medium, large-v3).
        device: Device to run on (cuda, cpu, auto).
        load_immediately: Whether to load the model immediately.
        
    Returns:
        Configured SpeechToText instance.
    """
    config = STTConfig(model_size=model_size, device=device)
    stt = SpeechToText(config)
    
    if load_immediately:
        stt.load_model()
    
    return stt
