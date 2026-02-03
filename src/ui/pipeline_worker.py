"""
Pipeline Worker - Background thread for running the voice pipeline.

Handles the async execution of the voice pipeline without blocking the UI.
"""

from PySide6.QtCore import QObject, QThread, Signal, Slot
from typing import Optional
import time

from src.pipeline import VoicePipeline, PipelineConfig, PipelineState, ConversationTurn


class PipelineWorker(QObject):
    """
    Worker that runs the voice pipeline in a background thread.
    
    Signals:
        state_changed(str): Emitted when pipeline state changes
        transcription_ready(str): Emitted when user speech is transcribed
        response_ready(str): Emitted when assistant response is generated
        error_occurred(str): Emitted on pipeline errors
        initialized: Emitted when pipeline is ready
        metrics_available(dict): Emitted with timing metrics after each turn
    """
    
    # Signals to communicate with UI
    state_changed = Signal(str)
    transcription_ready = Signal(str)
    response_ready = Signal(str)
    error_occurred = Signal(str)
    initialized = Signal()
    init_progress = Signal(str)
    metrics_available = Signal(dict)
    turn_complete = Signal()
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        super().__init__()
        
        self.config = config or PipelineConfig()
        self._pipeline: Optional[VoicePipeline] = None
        self._is_recording = False
        self._should_stop = False
    
    @Slot()
    def initialize(self):
        """Initialize the pipeline (runs in worker thread)."""
        try:
            self._pipeline = VoicePipeline(self.config)
            
            # Set up callbacks
            self._pipeline.set_callbacks(
                on_state_change=self._on_state_change,
                on_transcription=self._on_transcription,
                on_response=self._on_response
            )
            
            # Initialize with progress reporting
            success = self._pipeline.initialize(
                progress_callback=lambda msg: self.init_progress.emit(msg)
            )
            
            if success:
                self.initialized.emit()
            else:
                self.error_occurred.emit("Failed to initialize pipeline")
                
        except Exception as e:
            self.error_occurred.emit(f"Initialization error: {str(e)}")
    
    def _on_state_change(self, state: PipelineState):
        """Callback for pipeline state changes."""
        self.state_changed.emit(state.value)
    
    def _on_transcription(self, text: str):
        """Callback when transcription is ready."""
        self.transcription_ready.emit(text)
    
    def _on_response(self, text: str):
        """Callback when response is ready."""
        self.response_ready.emit(text)
    
    @Slot()
    def start_recording(self):
        """Start recording audio."""
        if not self._pipeline or not self._pipeline.is_initialized:
            self.error_occurred.emit("Pipeline not initialized")
            return
        
        if self._is_recording:
            return
        
        self._is_recording = True
        self.state_changed.emit("listening")
        
        try:
            # Start audio capture
            self._pipeline._audio_capture.start()
        except Exception as e:
            self.error_occurred.emit(f"Recording error: {str(e)}")
            self._is_recording = False
    
    @Slot()
    def stop_recording(self):
        """Stop recording and process the audio."""
        if not self._is_recording:
            return
        
        self._is_recording = False
        
        try:
            # Stop capture and get audio
            self._pipeline._audio_capture.stop()
            audio = self._pipeline._audio_capture.get_audio()
            
            # Immediately change state so button updates
            self.state_changed.emit("transcribing")
            
            if audio is None or len(audio) < 1000:
                self.state_changed.emit("idle")
                return
            
            # Process the audio through the pipeline
            self._process_audio(audio)
            
        except Exception as e:
            self.error_occurred.emit(f"Processing error: {str(e)}")
            self.state_changed.emit("error")
    
    def _process_audio(self, audio):
        """Process recorded audio through the full pipeline."""
        from src.pipeline import PipelineMetrics
        from src.llm.prompts import RAG_SYSTEM_PROMPT, NO_CONTEXT_PROMPT
        
        metrics = PipelineMetrics()
        
        try:
            print(">>> Starting audio processing")
            
            # 1. Transcribe
            self.state_changed.emit("transcribing")
            stt_start = time.time()
            transcription = self._pipeline._stt.transcribe(audio)
            metrics.stt_time = time.time() - stt_start
            
            user_text = transcription.text.strip()
            print(f">>> Transcribed: '{user_text}'")
            
            if not user_text:
                print(">>> Empty transcription, returning to idle")
                self.state_changed.emit("idle")
                return
            
            self.transcription_ready.emit(user_text)
            print(">>> Transcription signal emitted")
            
            # 2. RAG Retrieval (if enabled)
            context = ""
            if self._pipeline._retriever:
                print(">>> Starting RAG retrieval")
                self.state_changed.emit("retrieving")
                retrieval_start = time.time()
                try:
                    # RAG may have threading issues, so wrap carefully
                    import sys
                    sys.stdout.flush()
                    
                    context = self._pipeline._retriever.get_context(
                        user_text,
                        n_results=self.config.rag_n_results
                    )
                    metrics.retrieval_time = time.time() - retrieval_start
                    metrics.context_found = bool(context)
                    print(f">>> RAG retrieval complete, context found: {bool(context)}")
                except KeyboardInterrupt:
                    raise  # Don't catch Ctrl+C
                except SystemExit:
                    raise  # Don't catch exits
                except BaseException as e:
                    # Catch everything including crashes
                    print(f">>> RAG retrieval error (catching BaseException): {type(e).__name__}: {e}")
                    import traceback
                    traceback.print_exc()
                    # Continue without context
                    metrics.retrieval_time = time.time() - retrieval_start
                    metrics.context_found = False
                    context = ""
            
            # 3. Generate response
            print(">>> Starting LLM generation")
            self.state_changed.emit("thinking")
            llm_start = time.time()
            
            if context:
                system_prompt = RAG_SYSTEM_PROMPT.format(context=context)
            else:
                system_prompt = NO_CONTEXT_PROMPT if self._pipeline._retriever else None
            
            response = self._pipeline._llm.generate(user_text, system_prompt=system_prompt)
            metrics.llm_time = time.time() - llm_start
            
            assistant_text = response.text.strip()
            print(f">>> LLM response: '{assistant_text[:50]}...'")
            self.response_ready.emit(assistant_text)
            print(">>> Response signal emitted")
            
            # 4. Synthesize and play speech
            print(">>> Starting TTS")
            self.state_changed.emit("speaking")
            tts_start = time.time()
            tts_result = self._pipeline._tts.synthesize(assistant_text)
            metrics.tts_time = time.time() - tts_start
            print(">>> TTS complete, starting playback")
            
            # Play audio
            playback_start = time.time()
            self._pipeline._audio_playback.play(
                tts_result.audio,
                sample_rate=tts_result.sample_rate,
                blocking=True
            )
            metrics.playback_duration = time.time() - playback_start
            print(">>> Playback complete")
            
            # Report metrics
            self.metrics_available.emit(metrics.to_dict())
            
            # Done
            self.state_changed.emit("idle")
            self.turn_complete.emit()
            print(">>> Turn complete")
            
        except Exception as e:
            print(f">>> EXCEPTION in _process_audio: {e}")
            import traceback
            traceback.print_exc()
            self.error_occurred.emit(f"Processing error: {str(e)}")
            self.state_changed.emit("error")
            # Ensure we return to idle even on error
            import time as time_mod
            time_mod.sleep(3)
            self.state_changed.emit("idle")
    
    @Slot(str)
    def process_text_input(self, text: str):
        """Process a text input (skip recording/STT)."""
        if not self._pipeline or not self._pipeline.is_initialized:
            self.error_occurred.emit("Pipeline not initialized")
            return
        
        from src.pipeline import PipelineMetrics
        from src.llm.prompts import NO_CONTEXT_PROMPT
        
        metrics = PipelineMetrics()
        
        try:
            print(f">>> Processing text input: '{text}'")
            
            # Skip STT - already have text
            # Emit transcription to show user message in UI
            self.transcription_ready.emit(text)
            
            # Generate response (no RAG for now since it's disabled)
            print(">>> Starting LLM generation for text input")
            self.state_changed.emit("thinking")
            llm_start = time.time()
            
            response = self._pipeline._llm.generate(text, system_prompt=None)
            metrics.llm_time = time.time() - llm_start
            
            assistant_text = response.text.strip()
            print(f">>> LLM response: '{assistant_text[:50]}...'")
            self.response_ready.emit(assistant_text)
            print(">>> Response signal emitted")
            
            # Synthesize and play speech
            print(">>> Starting TTS")
            self.state_changed.emit("speaking")
            tts_start = time.time()
            tts_result = self._pipeline._tts.synthesize(assistant_text)
            metrics.tts_time = time.time() - tts_start
            print(">>> TTS complete, starting playback")
            
            # Play audio
            playback_start = time.time()
            self._pipeline._audio_playback.play(
                tts_result.audio,
                sample_rate=tts_result.sample_rate,
                blocking=True
            )
            metrics.playback_duration = time.time() - playback_start
            print(">>> Playback complete")
            
            # Report metrics
            self.metrics_available.emit(metrics.to_dict())
            
            # Done
            self.state_changed.emit("idle")
            self.turn_complete.emit()
            print(">>> Turn complete")
            
        except Exception as e:
            print(f">>> EXCEPTION in process_text_input: {e}")
            import traceback
            traceback.print_exc()
            self.error_occurred.emit(f"Error processing text: {str(e)}")
            self.state_changed.emit("error")
            # Return to idle after error
            import time as time_mod
            time_mod.sleep(3)
            self.state_changed.emit("idle")
    
    @Slot()
    def shutdown(self):
        """Shutdown the pipeline."""
        self._should_stop = True
        if self._pipeline:
            self._pipeline.shutdown()


class PipelineThread(QThread):
    """
    Dedicated thread for running the pipeline worker.
    
    Usage:
        thread = PipelineThread()
        thread.worker.initialized.connect(on_ready)
        thread.worker.state_changed.connect(on_state_change)
        thread.start()
        
        # Later:
        thread.worker.start_recording()
    """
    
    def __init__(self, config: Optional[PipelineConfig] = None, parent=None):
        super().__init__(parent)
        
        self.worker = PipelineWorker(config)
        self.worker.moveToThread(self)
        
        # Connect thread lifecycle
        self.started.connect(self.worker.initialize)
        self.finished.connect(self.worker.shutdown)
    
    def stop(self):
        """Stop the thread gracefully."""
        self.worker.shutdown()
        self.quit()
        self.wait(5000)  # Wait up to 5 seconds
