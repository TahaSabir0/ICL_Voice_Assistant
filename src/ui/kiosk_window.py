"""
Main Kiosk Window for the ICL Voice Assistant.

Full-screen application with push-to-talk button, state indicators,
and conversation display.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QFrame, QSizePolicy, QApplication, QStatusBar
)
from PySide6.QtCore import Qt, Signal, Slot, QThread, QObject
from PySide6.QtGui import QFont, QColor, QScreen

from .styles import MAIN_STYLESHEET, COLORS
from .widgets import PushToTalkButton, StateIndicator, ConversationView


class KioskWindow(QMainWindow):
    """
    Main kiosk window for the ICL Voice Assistant.
    
    Features:
    - Full-screen kiosk mode
    - Large push-to-talk button
    - State indicators (listening, thinking, speaking)
    - Conversation transcript display
    - Responsive layout
    
    Signals:
        ptt_pressed: Emitted when push-to-talk button is pressed
        ptt_released: Emitted when push-to-talk button is released
    """
    
    # Signals for external handling
    ptt_pressed = Signal()
    ptt_released = Signal()
    text_submitted = Signal(str)  # For typed messages
    
    def __init__(self, fullscreen: bool = True):
        super().__init__()
        
        self._fullscreen = fullscreen
        self._setup_window()
        self._setup_ui()
        self._apply_styles()
        
    def _setup_window(self):
        """Configure window properties."""
        self.setWindowTitle("ICL Voice Assistant")
        
        # Set window flags for kiosk mode
        if self._fullscreen:
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.WindowStaysOnTopHint
            )
            self.showFullScreen()
        else:
            self.setMinimumSize(1024, 768)
            self.resize(1280, 900)
    
    def _setup_ui(self):
        """Create the UI layout."""
        # Central widget
        central = QWidget()
        central.setObjectName("mainContainer")
        self.setCentralWidget(central)
        
        # Main layout
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(0)
        
        # === HEADER ===
        header = self._create_header()
        main_layout.addWidget(header)
        
        # === CONTENT AREA ===
        content_layout = QHBoxLayout()
        content_layout.setSpacing(40)
        
        # Left: Conversation panel with text input
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        # Conversation view
        self._conversation = ConversationView()
        self._conversation.setStyleSheet(f"""
            ConversationView {{
                background-color: {COLORS['surface']};
                border-radius: 20px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        left_layout.addWidget(self._conversation, 1)
        
        # Text input area
        from PySide6.QtWidgets import QLineEdit, QPushButton
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(10)
        
        self._text_input = QLineEdit()
        self._text_input.setPlaceholderText("Or type your question here...")
        self._text_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['surface']};
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
                padding: 12px 16px;
                color: {COLORS['text_primary']};
                font-size: 16px;
            }}
            QLineEdit:focus {{
                border-color: {COLORS['accent_primary']};
            }}
        """)
        self._text_input.returnPressed.connect(self._on_text_submitted)
        input_layout.addWidget(self._text_input, 1)
        
        self._send_button = QPushButton("Send")
        self._send_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_secondary']};
            }}
            QPushButton:pressed {{
                background-color: #3B8AE8;
            }}
            QPushButton:disabled {{
                background-color: {COLORS['surface_elevated']};
                color: {COLORS['text_muted']};
            }}
        """)
        self._send_button.clicked.connect(self._on_text_submitted)
        input_layout.addWidget(self._send_button)
        
        left_layout.addWidget(input_container)
        
        content_layout.addWidget(left_panel, 3)
        
        # Right: Button and state panel
        button_panel = self._create_button_panel()
        content_layout.addWidget(button_panel, 1)
        
        main_layout.addLayout(content_layout, 1)
        
        # === STATUS BAR ===
        self._status_bar = self._create_status_bar()
        main_layout.addWidget(self._status_bar)
    
    def _create_header(self) -> QWidget:
        """Create the header with title and state indicator."""
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(10, 0, 10, 20)
        
        # Title
        title = QLabel("ICL Voice Assistant")
        title.setObjectName("headerLabel")
        title.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 32px;
                font-weight: 700;
            }}
        """)
        layout.addWidget(title)
        
        layout.addStretch()
        
        # State indicator
        self._state_indicator = StateIndicator()
        layout.addWidget(self._state_indicator)
        
        return header
    
    def _create_button_panel(self) -> QWidget:
        """Create the right panel with push-to-talk button."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(30)
        
        layout.addStretch(1)
        
        # Instruction text
        instruction = QLabel("Press and hold to speak")
        instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_secondary']};
                font-size: 16px;
            }}
        """)
        layout.addWidget(instruction)
        
        # Push-to-talk button
        button_container = QHBoxLayout()
        button_container.addStretch()
        
        self._ptt_button = PushToTalkButton()
        self._ptt_button.pressed.connect(self._on_ptt_pressed)
        self._ptt_button.released.connect(self._on_ptt_released)
        button_container.addWidget(self._ptt_button)
        
        button_container.addStretch()
        layout.addLayout(button_container)
        
        # Hint text
        hint = QLabel("Or press spacebar")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_muted']};
                font-size: 14px;
            }}
        """)
        layout.addWidget(hint)
        
        layout.addStretch(1)
        
        return panel
    
    def _create_status_bar(self) -> QWidget:
        """Create the status bar at the bottom."""
        bar = QWidget()
        bar.setObjectName("statusBar")
        bar.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['surface']};
                border-radius: 8px;
                margin-top: 20px;
            }}
        """)
        
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 8, 16, 8)
        
        # Status text
        self._status_label = QLabel("System ready")
        self._status_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_secondary']};
                font-size: 14px;
            }}
        """)
        layout.addWidget(self._status_label)
        
        layout.addStretch()
        
        # Version/info
        version = QLabel("v0.1.0 • Innovation & Creativity Lab")
        version.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_muted']};
                font-size: 12px;
            }}
        """)
        layout.addWidget(version)
        
        return bar
    
    def _apply_styles(self):
        """Apply the main stylesheet."""
        self.setStyleSheet(MAIN_STYLESHEET)
    
    # === Event Handlers ===
    
    def _on_ptt_pressed(self):
        """Handle push-to-talk button pressed."""
        self.ptt_pressed.emit()
    
    def _on_ptt_released(self):
        """Handle push-to-talk button released."""
        self.ptt_released.emit()
    
    def _on_text_submitted(self):
        """Handle text input submission."""
        text = self._text_input.text().strip()
        if text:
            self.text_submitted.emit(text)
            self._text_input.clear()
    
    def keyPressEvent(self, event):
        """Handle keyboard events."""
        # Spacebar as alternative push-to-talk (only if text input doesn't have focus)
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            if not self._text_input.hasFocus():
                self._ptt_button.pressed.emit()
                self._on_ptt_pressed()
        
        # Escape to exit fullscreen (for development)
        elif event.key() == Qt.Key.Key_Escape:
            if self._fullscreen:
                self.close()
        
        super().keyPressEvent(event)
    
    def keyReleaseEvent(self, event):
        """Handle key release."""
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            if not self._text_input.hasFocus():
                self._ptt_button.released.emit()
                self._on_ptt_released()
        
        super().keyReleaseEvent(event)
    
    # === Public API ===
    
    def set_state(self, state: str):
        """
        Update the UI state.
        
        Args:
            state: One of 'idle', 'listening', 'transcribing', 
                   'retrieving', 'thinking', 'speaking', 'error'
        """
        self._state_indicator.set_state(state)
        self._ptt_button.set_state(state)
        
        # Show/hide thinking indicator
        if state in ("transcribing", "retrieving", "thinking"):
            self._conversation.show_thinking()
        else:
            self._conversation.hide_thinking()
    
    def add_user_message(self, text: str):
        """Add a user message to the conversation."""
        self._conversation.add_message("user", text)
    
    def add_assistant_message(self, text: str):
        """Add an assistant message to the conversation."""
        self._conversation.hide_thinking()
        self._conversation.add_message("assistant", text)
    
    def set_status(self, text: str):
        """Update the status bar text."""
        self._status_label.setText(text)
    
    def clear_conversation(self):
        """Clear the conversation history."""
        self._conversation.clear()
    
    @property
    def ptt_button(self) -> PushToTalkButton:
        """Access the push-to-talk button."""
        return self._ptt_button
    
    @property
    def state_indicator(self) -> StateIndicator:
        """Access the state indicator."""
        return self._state_indicator
    
    @property
    def conversation_view(self) -> ConversationView:
        """Access the conversation view."""
        return self._conversation


def launch_kiosk(fullscreen: bool = True) -> int:
    """
    Launch the kiosk application.
    
    Args:
        fullscreen: Whether to run in fullscreen mode.
        
    Returns:
        Application exit code.
    """
    import sys
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Set application font
    font = QFont("Inter", 10)
    app.setFont(font)
    
    # Create and show window
    window = KioskWindow(fullscreen=fullscreen)
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    # Test the kiosk in windowed mode
    launch_kiosk(fullscreen=False)
