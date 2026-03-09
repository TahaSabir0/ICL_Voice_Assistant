"""
Pipeline Worker - Background thread for running the voice pipeline.

Handles the async execution of the voice pipeline without blocking the UI.
"""

from PySide6.QtCore import QObject, QThread, Signal, Slot
from typing import Optional
import time

from src.pipeline import VoicePipeline, PipelineConfig, PipelineState, ConversationTurn
from src.rag.subprocess_retriever import SubprocessRetriever


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
        self._subprocess_retriever: Optional[SubprocessRetriever] = None
        self._is_recording = False
        self._should_stop = False

    @Slot()
    def initialize(self):
        """Initialize the pipeline (runs in worker thread)."""
        try:
            # Disable in-process RAG — it will be handled by SubprocessRetriever
            config_copy = PipelineConfig(
                stt_model=self.config.stt_model,
                stt_device=self.config.stt_device,
                llm_model=self.config.llm_model,
                llm_temperature=self.config.llm_temperature,
                llm_max_tokens=self.config.llm_max_tokens,
                tts_backend=self.config.tts_backend,
                tts_rate=self.config.tts_rate,
                silence_threshold=self.config.silence_threshold,
                silence_duration=self.config.silence_duration,
                max_recording_duration=self.config.max_recording_duration,
                use_rag=False,  # Disable in-process RAG to avoid segfault
                rag_n_results=self.config.rag_n_results,
                rag_relevance_threshold=self.config.rag_relevance_threshold,
            )

            self._pipeline = VoicePipeline(config_copy)

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

            if not success:
                self.error_occurred.emit("Failed to initialize pipeline")
                return

            # Initialize RAG in a subprocess (isolated from Qt)
            if self.config.use_rag:
                try:
                    self._subprocess_retriever = SubprocessRetriever(
                        relevance_threshold=self.config.rag_relevance_threshold
                    )
                    rag_ok = self._subprocess_retriever.start(
                        progress_callback=lambda msg: self.init_progress.emit(msg)
                    )
                    if not rag_ok:
                        self.init_progress.emit("  RAG unavailable (continuing without)")
                        self._subprocess_retriever = None
                except Exception as e:
                    self.init_progress.emit(f"  RAG subprocess failed: {e}")
                    self._subprocess_retriever = None

            self.initialized.emit()

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
            
            # 2. RAG Retrieval via subprocess (isolated from Qt)
            context = ""
            if self._subprocess_retriever and self._subprocess_retriever.is_ready:
                print(">>> Starting RAG retrieval (subprocess)")
                self.state_changed.emit("retrieving")
                rag_start = time.time()
                context = self._subprocess_retriever.get_context(
                    user_text, n_results=self.config.rag_n_results
                )
                metrics.retrieval_time = time.time() - rag_start
                if context:
                    print(f">>> RAG found {len(context)} chars of context")
                else:
                    print(">>> No relevant context found")
            else:
                print(">>> RAG not available")

            # 3. Generate response
            print(">>> Starting LLM generation")
            self.state_changed.emit("thinking")
            llm_start = time.time()
            
            if context:
                system_prompt = RAG_SYSTEM_PROMPT.format(context=context)
            else:
                system_prompt = NO_CONTEXT_PROMPT if self._subprocess_retriever else None
            
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
            QThread.msleep(3000)
            self.state_changed.emit("idle")
    
    @Slot(str)
    def process_text_input(self, text: str):
        """Process a text input (skip recording/STT)."""
        if not self._pipeline or not self._pipeline.is_initialized:
            self.error_occurred.emit("Pipeline not initialized")
            return
        
        from src.pipeline import PipelineMetrics

        metrics = PipelineMetrics()
        
        try:
            print(f">>> Processing text input: '{text}'")

            # Skip STT - already have text
            self.transcription_ready.emit(text)

            # RAG Retrieval via subprocess (isolated from Qt)
            context = ""
            if self._subprocess_retriever and self._subprocess_retriever.is_ready:
                print(">>> Starting RAG retrieval for text input (subprocess)")
                self.state_changed.emit("retrieving")
                rag_start = time.time()
                context = self._subprocess_retriever.get_context(
                    text, n_results=self.config.rag_n_results
                )
                metrics.retrieval_time = time.time() - rag_start
                if context:
                    print(f">>> RAG found {len(context)} chars of context")
                else:
                    print(">>> No relevant context found")
            else:
                print(">>> RAG not available")

            # Generate response
            print(">>> Starting LLM generation for text input")
            self.state_changed.emit("thinking")
            llm_start = time.time()

            from src.llm.prompts import RAG_SYSTEM_PROMPT, NO_CONTEXT_PROMPT
            if context:
                system_prompt = RAG_SYSTEM_PROMPT.format(context=context)
            elif self._subprocess_retriever:
                system_prompt = NO_CONTEXT_PROMPT
            else:
                system_prompt = None

            response = self._pipeline._llm.generate(text, system_prompt=system_prompt)
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
            QThread.msleep(3000)
            self.state_changed.emit("idle")
    
    @Slot()
    def shutdown(self):
        """Shutdown the pipeline and subprocess retriever."""
        self._should_stop = True
        if self._subprocess_retriever:
            self._subprocess_retriever.stop()
            self._subprocess_retriever = None
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
