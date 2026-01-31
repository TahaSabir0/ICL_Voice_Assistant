"""
Voice Pipeline - Main orchestration for the ICL Voice Assistant.

Wires together: Audio Capture → STT → LLM → TTS → Audio Playback
"""

import time
from dataclasses import dataclass, field
from typing import Optional, Callable, Dict, Any
from enum import Enum
import threading

from src.audio import AudioCapture, AudioPlayback, AudioConfig
from src.stt import SpeechToText, STTConfig
from src.tts import TextToSpeech, TTSConfig, TTSBackend
from src.llm import LLMClient, LLMConfig


class PipelineState(Enum):
    """States for the voice pipeline."""
    IDLE = "idle"
    LISTENING = "listening"
    TRANSCRIBING = "transcribing"
    THINKING = "thinking"
    SPEAKING = "speaking"
    ERROR = "error"


@dataclass
class PipelineConfig:
    """Configuration for the voice pipeline."""
    # STT settings
    stt_model: str = "base"  # tiny, base, small, medium
    stt_device: str = "auto"
    
    # LLM settings
    llm_model: str = "llama3.1:8b-instruct-q4_K_M"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 256  # Keep responses short for voice
    
    # TTS settings
    tts_backend: TTSBackend = TTSBackend.PYTTSX3
    tts_rate: int = 160  # Slightly faster speech
    
    # Audio settings
    silence_threshold: float = 0.01
    silence_duration: float = 1.5
    max_recording_duration: float = 15.0


@dataclass
class PipelineMetrics:
    """Timing metrics for a single pipeline run."""
    recording_duration: float = 0.0
    stt_time: float = 0.0
    llm_time: float = 0.0
    tts_time: float = 0.0
    playback_duration: float = 0.0
    
    @property
    def total_processing_time(self) -> float:
        """Total time from end of recording to start of playback."""
        return self.stt_time + self.llm_time + self.tts_time
    
    @property
    def end_to_end_time(self) -> float:
        """Total time from start of recording to end of playback."""
        return self.recording_duration + self.stt_time + self.llm_time + self.tts_time + self.playback_duration
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "recording": self.recording_duration,
            "stt": self.stt_time,
            "llm": self.llm_time,
            "tts": self.tts_time,
            "playback": self.playback_duration,
            "processing": self.total_processing_time,
            "end_to_end": self.end_to_end_time,
        }


@dataclass
class ConversationTurn:
    """A single turn in the conversation."""
    user_audio_duration: float
    user_text: str
    assistant_text: str
    assistant_audio_duration: float
    metrics: PipelineMetrics
    timestamp: float = field(default_factory=time.time)


class VoicePipeline:
    """
    Main voice pipeline for the ICL Voice Assistant.
    
    Orchestrates: Audio → STT → LLM → TTS → Playback
    
    Usage:
        pipeline = VoicePipeline()
        pipeline.initialize()  # Load all models
        
        # Process a single turn
        result = pipeline.process_turn()
        print(f"User: {result.user_text}")
        print(f"Assistant: {result.assistant_text}")
        print(f"Latency: {result.metrics.total_processing_time:.2f}s")
    """
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        
        # Components
        self._audio_capture: Optional[AudioCapture] = None
        self._audio_playback: Optional[AudioPlayback] = None
        self._stt: Optional[SpeechToText] = None
        self._llm: Optional[LLMClient] = None
        self._tts: Optional[TextToSpeech] = None
        
        # State
        self._state = PipelineState.IDLE
        self._is_initialized = False
        self._conversation_history: list = []
        
        # Callbacks
        self._on_state_change: Optional[Callable[[PipelineState], None]] = None
        self._on_transcription: Optional[Callable[[str], None]] = None
        self._on_response: Optional[Callable[[str], None]] = None
    
    @property
    def state(self) -> PipelineState:
        """Current pipeline state."""
        return self._state
    
    @property
    def is_initialized(self) -> bool:
        """Whether all components are loaded."""
        return self._is_initialized
    
    @property
    def conversation_history(self) -> list:
        """List of conversation turns."""
        return self._conversation_history
    
    def set_callbacks(
        self,
        on_state_change: Optional[Callable[[PipelineState], None]] = None,
        on_transcription: Optional[Callable[[str], None]] = None,
        on_response: Optional[Callable[[str], None]] = None
    ):
        """Set callback functions for pipeline events."""
        self._on_state_change = on_state_change
        self._on_transcription = on_transcription
        self._on_response = on_response
    
    def _set_state(self, state: PipelineState):
        """Update state and notify callback."""
        self._state = state
        if self._on_state_change:
            self._on_state_change(state)
    
    def initialize(self, progress_callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Initialize all pipeline components.
        
        Args:
            progress_callback: Optional callback for progress updates.
            
        Returns:
            True if all components initialized successfully.
        """
        def report(msg: str):
            print(msg)
            if progress_callback:
                progress_callback(msg)
        
        try:
            # Initialize audio capture
            report("Initializing audio capture...")
            audio_config = AudioConfig(
                silence_threshold=self.config.silence_threshold,
                silence_duration=self.config.silence_duration,
                max_duration=self.config.max_recording_duration
            )
            self._audio_capture = AudioCapture(audio_config)
            
            # Initialize audio playback
            report("Initializing audio playback...")
            self._audio_playback = AudioPlayback()
            
            # Initialize STT
            report(f"Loading STT model ({self.config.stt_model})...")
            stt_config = STTConfig(
                model_size=self.config.stt_model,
                device=self.config.stt_device,
                compute_type="int8" if self.config.stt_device == "cpu" else "float16"
            )
            self._stt = SpeechToText(stt_config)
            if not self._stt.load_model():
                raise RuntimeError("Failed to load STT model")
            
            # Initialize LLM
            report(f"Connecting to LLM ({self.config.llm_model})...")
            llm_config = LLMConfig(
                model=self.config.llm_model,
                temperature=self.config.llm_temperature,
                max_tokens=self.config.llm_max_tokens
            )
            self._llm = LLMClient(llm_config)
            if not self._llm.check_availability():
                raise RuntimeError(f"LLM model not available: {self.config.llm_model}")
            
            # Initialize TTS
            report("Loading TTS engine...")
            tts_config = TTSConfig(
                backend=self.config.tts_backend,
                rate=self.config.tts_rate
            )
            self._tts = TextToSpeech(tts_config)
            if not self._tts.load_voice():
                raise RuntimeError("Failed to load TTS voice")
            
            self._is_initialized = True
            report("Pipeline initialized successfully!")
            return True
            
        except Exception as e:
            report(f"Initialization failed: {e}")
            self._is_initialized = False
            return False
    
    def process_turn(self, auto_record: bool = True) -> Optional[ConversationTurn]:
        """
        Process a single conversation turn.
        
        Args:
            auto_record: If True, start recording automatically.
            
        Returns:
            ConversationTurn with results and metrics, or None on error.
        """
        if not self._is_initialized:
            raise RuntimeError("Pipeline not initialized. Call initialize() first.")
        
        metrics = PipelineMetrics()
        
        try:
            # 1. Record audio
            self._set_state(PipelineState.LISTENING)
            print("\n🎤 Listening... (speak now)")
            
            record_start = time.time()
            self._audio_capture.start()
            self._audio_capture.wait_for_completion()
            audio = self._audio_capture.get_audio()
            metrics.recording_duration = time.time() - record_start
            
            if audio is None or len(audio) < 1000:  # Too short
                print("No audio captured")
                self._set_state(PipelineState.IDLE)
                return None
            
            print(f"   Recorded {metrics.recording_duration:.2f}s of audio")
            
            # 2. Transcribe
            self._set_state(PipelineState.TRANSCRIBING)
            print("📝 Transcribing...")
            
            stt_start = time.time()
            transcription = self._stt.transcribe(audio)
            metrics.stt_time = time.time() - stt_start
            
            user_text = transcription.text.strip()
            print(f"   User: \"{user_text}\"")
            print(f"   STT took {metrics.stt_time:.2f}s")
            
            if self._on_transcription:
                self._on_transcription(user_text)
            
            if not user_text:
                print("No speech detected")
                self._set_state(PipelineState.IDLE)
                return None
            
            # 3. Generate response
            self._set_state(PipelineState.THINKING)
            print("🤔 Thinking...")
            
            llm_start = time.time()
            response = self._llm.generate(user_text)
            metrics.llm_time = time.time() - llm_start
            
            assistant_text = response.text.strip()
            print(f"   Assistant: \"{assistant_text}\"")
            print(f"   LLM took {metrics.llm_time:.2f}s")
            
            if self._on_response:
                self._on_response(assistant_text)
            
            # 4. Synthesize speech
            self._set_state(PipelineState.SPEAKING)
            print("🔊 Speaking...")
            
            tts_start = time.time()
            tts_result = self._tts.synthesize(assistant_text)
            metrics.tts_time = time.time() - tts_start
            
            print(f"   TTS took {metrics.tts_time:.2f}s")
            
            # 5. Play audio
            playback_start = time.time()
            self._audio_playback.play(
                tts_result.audio,
                sample_rate=tts_result.sample_rate,
                blocking=True
            )
            metrics.playback_duration = time.time() - playback_start
            
            # Create turn record
            turn = ConversationTurn(
                user_audio_duration=metrics.recording_duration,
                user_text=user_text,
                assistant_text=assistant_text,
                assistant_audio_duration=tts_result.duration,
                metrics=metrics
            )
            
            self._conversation_history.append(turn)
            
            # Report metrics
            print(f"\n⏱️  Metrics:")
            print(f"   Processing time: {metrics.total_processing_time:.2f}s")
            print(f"   (STT: {metrics.stt_time:.2f}s, LLM: {metrics.llm_time:.2f}s, TTS: {metrics.tts_time:.2f}s)")
            
            self._set_state(PipelineState.IDLE)
            return turn
            
        except Exception as e:
            print(f"Error in pipeline: {e}")
            self._set_state(PipelineState.ERROR)
            import traceback
            traceback.print_exc()
            return None
    
    def process_text(self, text: str) -> Optional[ConversationTurn]:
        """
        Process a text input (skip recording and STT).
        
        Useful for testing the LLM and TTS components.
        
        Args:
            text: User's text input.
            
        Returns:
            ConversationTurn with results and metrics.
        """
        if not self._is_initialized:
            raise RuntimeError("Pipeline not initialized. Call initialize() first.")
        
        metrics = PipelineMetrics()
        
        try:
            user_text = text.strip()
            print(f"\n📝 Input: \"{user_text}\"")
            
            if self._on_transcription:
                self._on_transcription(user_text)
            
            # Generate response
            self._set_state(PipelineState.THINKING)
            print("🤔 Thinking...")
            
            llm_start = time.time()
            response = self._llm.generate(user_text)
            metrics.llm_time = time.time() - llm_start
            
            assistant_text = response.text.strip()
            print(f"   Assistant: \"{assistant_text}\"")
            print(f"   LLM took {metrics.llm_time:.2f}s")
            
            if self._on_response:
                self._on_response(assistant_text)
            
            # Synthesize speech
            self._set_state(PipelineState.SPEAKING)
            print("🔊 Speaking...")
            
            tts_start = time.time()
            tts_result = self._tts.synthesize(assistant_text)
            metrics.tts_time = time.time() - tts_start
            
            print(f"   TTS took {metrics.tts_time:.2f}s")
            
            # Play audio
            playback_start = time.time()
            self._audio_playback.play(
                tts_result.audio,
                sample_rate=tts_result.sample_rate,
                blocking=True
            )
            metrics.playback_duration = time.time() - playback_start
            
            # Create turn record
            turn = ConversationTurn(
                user_audio_duration=0,
                user_text=user_text,
                assistant_text=assistant_text,
                assistant_audio_duration=tts_result.duration,
                metrics=metrics
            )
            
            self._conversation_history.append(turn)
            
            print(f"\n⏱️  Processing time: {metrics.total_processing_time:.2f}s")
            
            self._set_state(PipelineState.IDLE)
            return turn
            
        except Exception as e:
            print(f"Error in pipeline: {e}")
            self._set_state(PipelineState.ERROR)
            return None
    
    def shutdown(self):
        """Shutdown all components and free resources."""
        print("Shutting down pipeline...")
        
        if self._stt:
            self._stt.unload_model()
        
        if self._tts:
            self._tts.unload_voice()
        
        self._is_initialized = False
        self._set_state(PipelineState.IDLE)
        
        print("Pipeline shutdown complete.")


def create_pipeline(config: Optional[PipelineConfig] = None) -> VoicePipeline:
    """
    Factory function to create a voice pipeline.
    
    Args:
        config: Optional pipeline configuration.
        
    Returns:
        Configured VoicePipeline instance (not yet initialized).
    """
    return VoicePipeline(config)
