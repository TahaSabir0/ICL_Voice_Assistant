"""
Main Kiosk Application - Full integration of UI and Voice Pipeline.

This is the main entry point for the ICL Voice Assistant kiosk.
"""

import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor

from src.ui.kiosk_window import KioskWindow
from src.ui.pipeline_worker import PipelineThread
from src.ui.error_handling import (
    setup_logging, HealthMonitor, MemoryMonitor, Watchdog,
    categorize_error, get_recovery_action, RecoveryAction
)
from src.pipeline import PipelineConfig

# Module logger
logger = logging.getLogger(__name__)


class KioskApplication:
    """
    Main kiosk application that integrates UI with the voice pipeline.
    
    Manages:
    - Qt application lifecycle
    - Pipeline thread management
    - UI/Pipeline signal connections
    - Error handling and recovery
    - Health monitoring
    """
    
    def __init__(
        self,
        fullscreen: bool = True,
        use_rag: bool = True,
        llm_model: str = "llama3.1:8b-instruct-q4_K_M",
        enable_watchdog: bool = True
    ):
        """
        Initialize the kiosk application.
        
        Args:
            fullscreen: Run in fullscreen kiosk mode
            use_rag: Enable RAG retrieval from knowledge base
            llm_model: Ollama model to use for responses
            enable_watchdog: Enable watchdog timer for hang detection
        """
        self.fullscreen = fullscreen
        self.use_rag = use_rag
        self.llm_model = llm_model
        
        # Setup logging
        project_root = Path(__file__).parent.parent.parent
        log_file = setup_logging(project_root / "logs")
        logger.info(f"Kiosk application starting. Log file: {log_file}")
        
        # Create application
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)
        
        # Set application-wide font
        font = QFont("Inter", 10)
        self.app.setFont(font)
        
        # Components
        self.window: KioskWindow = None
        self.pipeline_thread: PipelineThread = None
        self._is_recording = False
        
        # Monitoring
        self.health_monitor = HealthMonitor(unhealthy_threshold=300.0)
        self.memory_monitor = MemoryMonitor(warning_threshold_mb=2000.0)
        
        # Watchdog for hang detection
        if enable_watchdog:
            self.watchdog = Watchdog(
                timeout=120.0,  # 2 minutes without activity triggers watchdog
                on_timeout=self._on_watchdog_timeout
            )
        else:
            self.watchdog = None
        
        # Track errors for recovery
        self._consecutive_errors = 0
        self._max_consecutive_errors = 5
        
    def run(self) -> int:
        """
        Run the kiosk application.
        
        Returns:
            Exit code
        """
        # Configure pipeline
        config = PipelineConfig(
            use_rag=self.use_rag,
            llm_model=self.llm_model
        )
        
        self._splash = None  # No splash screen
        
        self.pipeline_thread = PipelineThread(config)
        
        # IMPORTANT: Connect signals BEFORE starting thread to avoid race condition
        # Use Qt.QueuedConnection for cross-thread signals
        self._connect_pipeline_signals()
        
        # Connect initialization complete - use QueuedConnection for thread safety
        self.pipeline_thread.worker.initialized.connect(
            self._on_pipeline_ready,
            Qt.ConnectionType.QueuedConnection
        )
        
        # Connect init progress to splash
        self.pipeline_thread.worker.init_progress.connect(
            self._update_splash_message,
            Qt.ConnectionType.QueuedConnection
        )
        
        # Handle init failure
        self.pipeline_thread.worker.error_occurred.connect(
            self._on_init_error,
            Qt.ConnectionType.QueuedConnection
        )
        
        # NOW start the thread (after all signals connected)
        self.pipeline_thread.start()
        
        # Create and show main window immediately (shows loading status)
        self.window = KioskWindow(fullscreen=self.fullscreen)
        self._connect_window_signals()
        
        # Show window with loading status
        self.window.set_status("Initializing voice pipeline...")
        self.window.set_state("thinking")  # Show loading animation
        self.window.show()
        
        return self.app.exec()
    
    @Slot(str)
    def _update_splash_message(self, msg: str):
        """Update the splash screen message."""
        if hasattr(self, '_splash') and self._splash:
            self._splash.showMessage(
                msg, 
                Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, 
                QColor(255, 255, 255)
            )
    
    def _create_splash(self) -> QSplashScreen:
        """Create a splash screen for loading."""
        # Create a simple splash pixmap
        pixmap = QPixmap(600, 400)
        pixmap.fill(QColor("#0D1117"))
        
        painter = QPainter(pixmap)
        painter.setPen(QColor("#F0F6FC"))
        font = QFont("Inter", 24, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "ICL Voice Assistant")
        
        font = QFont("Inter", 14)
        painter.setFont(font)
        painter.setPen(QColor("#8B949E"))
        painter.drawText(
            pixmap.rect().adjusted(0, 60, 0, 0), 
            Qt.AlignmentFlag.AlignCenter, 
            "Loading..."
        )
        painter.end()
        
        splash = QSplashScreen(pixmap)
        splash.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        return splash
    
    def _connect_pipeline_signals(self):
        """Connect pipeline worker signals to handlers."""
        worker = self.pipeline_thread.worker
        
        # All connections use QueuedConnection for thread safety
        # This ensures slots run in the main UI thread
        worker.state_changed.connect(
            self._on_state_changed, 
            Qt.ConnectionType.QueuedConnection
        )
        worker.transcription_ready.connect(
            self._on_transcription,
            Qt.ConnectionType.QueuedConnection
        )
        worker.response_ready.connect(
            self._on_response,
            Qt.ConnectionType.QueuedConnection
        )
        worker.error_occurred.connect(
            self._on_error,
            Qt.ConnectionType.QueuedConnection
        )
        worker.metrics_available.connect(
            self._on_metrics,
            Qt.ConnectionType.QueuedConnection
        )
        worker.turn_complete.connect(
            self._on_turn_complete,
            Qt.ConnectionType.QueuedConnection
        )
    
    def _connect_window_signals(self):
        """Connect window signals to pipeline."""
        self.window.ptt_pressed.connect(self._on_ptt_pressed)
        self.window.ptt_released.connect(self._on_ptt_released)
        # Connect text submission directly to worker (thread-safe signal)
        self.window.text_submitted.connect(
            self.pipeline_thread.worker.process_text_input,
            Qt.ConnectionType.QueuedConnection
        )
    
    @Slot()
    def _on_pipeline_ready(self):
        """Handle pipeline initialization complete."""
        print(">>> _on_pipeline_ready called")
        logger.info("Pipeline ready")
        
        try:
            # Close splash if still open
            if hasattr(self, '_splash') and self._splash:
                self._splash.close()
                self._splash = None
            
            # Update window status (window is already visible)
            if self.window:
                self.window.set_status("Ready - Press the button to speak")
                self.window.set_state("idle")
                print(">>> Window updated to ready state")
            
            # Start monitoring
            self.memory_monitor.set_baseline()
            if self.watchdog:
                self.watchdog.start()
            
            # Record activity for health monitor
            self.health_monitor.record_activity()
            print(">>> _on_pipeline_ready complete")
            
        except Exception as e:
            print(f">>> EXCEPTION in _on_pipeline_ready: {e}")
            import traceback
            traceback.print_exc()
    
    @Slot(str)
    def _on_init_error(self, error: str):
        """Handle pipeline initialization failure."""
        logger.error(f"Pipeline initialization failed: {error}")
        
        if hasattr(self, '_splash') and self._splash:
            self._splash.close()
            self._splash = None
        
        QMessageBox.critical(
            None,
            "Initialization Error",
            f"Failed to start the voice assistant:\n\n{error}\n\n"
            "Please check that Ollama is running and try again."
        )
        
        self.app.quit()
    
    @Slot(str)
    def _on_state_changed(self, state: str):
        """Handle pipeline state changes."""
        if self.window:
            self.window.set_state(state)
            
            # Update status text
            status_map = {
                "idle": "Ready - Press the button to speak",
                "listening": "Listening... Release when done",
                "transcribing": "Processing your speech...",
                "retrieving": "Searching knowledge base...",
                "thinking": "Generating response...",
                "speaking": "Speaking response...",
                "error": "An error occurred"
            }
            self.window.set_status(status_map.get(state, state))
        
        # Ping watchdog on state changes
        if self.watchdog:
            self.watchdog.ping()
    
    @Slot(str)
    def _on_transcription(self, text: str):
        """Handle transcription ready."""
        print(f">>> _on_transcription received: '{text}'")
        if self.window:
            self.window.add_user_message(text)
            print(">>> User message added to conversation")
    
    @Slot(str)
    def _on_response(self, text: str):
        """Handle response ready."""
        print(f">>> _on_response received: '{text[:50]}...'")
        if self.window:
            self.window.add_assistant_message(text)
            print(">>> Assistant message added to conversation")
    
    @Slot(str)
    def _on_error(self, error: str):
        """Handle pipeline errors."""
        logger.error(f"Pipeline error: {error}")
        
        # Track error in health monitor
        self.health_monitor.record_error()
        self._consecutive_errors += 1
        
        if self.window:
            self.window.set_status(f"Error: {error}")
            
            # Reset to idle after a delay
            QTimer.singleShot(3000, lambda: self.window.set_state("idle"))
        
        # Check if we need to take recovery action
        if self._consecutive_errors >= self._max_consecutive_errors:
            logger.warning(f"Too many consecutive errors ({self._consecutive_errors}), attempting recovery")
            self._attempt_recovery()
    
    @Slot(dict)
    def _on_metrics(self, metrics: dict):
        """Handle timing metrics."""
        processing_time = metrics.get("processing", 0)
        self.window.set_status(f"Completed in {processing_time:.1f}s - Press button to speak again")
    
    @Slot()
    def _on_turn_complete(self):
        """Handle conversation turn complete."""
        logger.debug("Turn completed successfully")
        
        # Reset consecutive error counter on success
        self._consecutive_errors = 0
        
        # Record activity for health monitoring
        self.health_monitor.record_activity()
        
        # Ping watchdog
        if self.watchdog:
            self.watchdog.ping()
        
        # Check memory periodically
        mem_status = self.memory_monitor.check_memory()
        if mem_status.get("warning"):
            logger.warning(f"High memory usage: {mem_status['current_mb']:.1f} MB")
    
    @Slot()
    def _on_ptt_pressed(self):
        """Handle push-to-talk button pressed."""
        print(">>> PTT pressed")
        if self._is_recording:
            return
        
        self._is_recording = True
        
        # Invoke worker method in worker's thread
        from PySide6.QtCore import QMetaObject, Qt
        QMetaObject.invokeMethod(
            self.pipeline_thread.worker,
            "start_recording",
            Qt.ConnectionType.QueuedConnection
        )
    
    @Slot()
    def _on_ptt_released(self):
        """Handle push-to-talk button released."""
        print(">>> PTT released")
        if not self._is_recording:
            return
        
        self._is_recording = False
        
        # Invoke worker method in worker's thread
        from PySide6.QtCore import QMetaObject, Qt
        QMetaObject.invokeMethod(
            self.pipeline_thread.worker,
            "stop_recording",
            Qt.ConnectionType.QueuedConnection
        )
    
    # Text submission is now handled via direct signal connection in _connect_window_signals
    
    def _on_watchdog_timeout(self):
        """Handle watchdog timeout (system hang detected)."""
        logger.error("Watchdog timeout! System appears to be hung.")
        
        # Log health status
        health = self.health_monitor.get_status()
        logger.error(f"Health status: {health}")
        
        # Attempt recovery by resetting state
        if self.window:
            self.window.set_state("error")
            self.window.set_status("System recovering...")
            
            # Force reset to idle
            QTimer.singleShot(2000, self._reset_to_idle)
    
    def _reset_to_idle(self):
        """Reset the application to idle state."""
        logger.info("Resetting to idle state")
        self._is_recording = False
        if self.window:
            self.window.set_state("idle")
            self.window.set_status("Ready - Press the button to speak")
    
    def _attempt_recovery(self):
        """Attempt to recover from multiple consecutive errors."""
        logger.info("Attempting error recovery...")
        
        # Reset consecutive error counter
        self._consecutive_errors = 0
        
        # Reset to idle state
        self._reset_to_idle()
        
        # Clear conversation if too many errors
        if self.window:
            self.window.set_status("System recovered - please try again")
    
    def shutdown(self):
        """Gracefully shutdown the application."""
        logger.info("Shutting down kiosk application...")
        
        # Stop watchdog
        if self.watchdog:
            self.watchdog.stop()
        
        # Log final health status
        health = self.health_monitor.get_status()
        logger.info(f"Final health status: {health}")
        
        # Stop pipeline
        if self.pipeline_thread:
            self.pipeline_thread.stop()
        
        if self.window:
            self.window.close()
        
        logger.info("Shutdown complete")


def main():
    """Main entry point for the kiosk application."""
    import argparse
    
    parser = argparse.ArgumentParser(description="ICL Voice Assistant Kiosk")
    parser.add_argument(
        "--windowed", "-w",
        action="store_true",
        help="Run in windowed mode instead of fullscreen"
    )
    parser.add_argument(
        "--no-rag",
        action="store_true",
        help="Disable RAG retrieval (use basic LLM only)"
    )
    parser.add_argument(
        "--model", "-m",
        default="llama3.1:8b-instruct-q4_K_M",
        help="Ollama model to use (default: llama3.1:8b-instruct-q4_K_M)"
    )
    
    args = parser.parse_args()
    
    app = KioskApplication(
        fullscreen=not args.windowed,
        use_rag=not args.no_rag,
        llm_model=args.model
    )
    
    try:
        return app.run()
    except KeyboardInterrupt:
        app.shutdown()
        return 0
    except Exception as e:
        print(f"Fatal error: {e}")
        app.shutdown()
        return 1


if __name__ == "__main__":
    sys.exit(main())
