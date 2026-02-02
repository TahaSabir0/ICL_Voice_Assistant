"""
State Indicator Widget.

Displays the current state of the voice assistant with animated text
and visual feedback.
"""

from PySide6.QtWidgets import QLabel, QHBoxLayout, QWidget
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, Property, 
    QTimer, Signal
)
from PySide6.QtGui import QColor


class StateIndicator(QWidget):
    """
    Visual indicator for the current pipeline state.
    
    Shows:
    - State name (Ready, Listening, Thinking, Speaking)
    - Animated dots for active states
    - Color-coded background
    """
    
    STATE_TEXT = {
        "idle": "Ready to assist",
        "listening": "Listening",
        "transcribing": "Processing speech",
        "retrieving": "Searching knowledge base",
        "thinking": "Thinking",
        "speaking": "Speaking",
        "error": "Error occurred",
    }
    
    STATE_ICONS = {
        "idle": "🟢",
        "listening": "🎤",
        "transcribing": "📝",
        "retrieving": "🔍",
        "thinking": "💭",
        "speaking": "🔊",
        "error": "⚠️",
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._state = "idle"
        self._dot_count = 0
        
        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Icon label
        self._icon_label = QLabel()
        self._icon_label.setObjectName("stateIcon")
        self._icon_label.setStyleSheet("font-size: 24px;")
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._icon_label)
        
        # State text label
        self._label = QLabel()
        self._label.setObjectName("stateLabel")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label)
        
        # Animation timer for dots
        self._dot_timer = QTimer(self)
        self._dot_timer.timeout.connect(self._update_dots)
        
        # Set initial state
        self.set_state("idle")
    
    @property
    def state(self):
        return self._state
    
    def set_state(self, state: str):
        """
        Update the displayed state.
        
        Args:
            state: One of the pipeline states
        """
        self._state = state
        self._dot_count = 0
        
        # Update icon
        icon = self.STATE_ICONS.get(state, "")
        self._icon_label.setText(icon)
        
        # Update text
        text = self.STATE_TEXT.get(state, state.title())
        self._label.setText(text)
        
        # Update property for styling
        self._label.setProperty("state", state)
        self._label.style().unpolish(self._label)
        self._label.style().polish(self._label)
        
        # Start/stop dot animation for active states
        if state in ("listening", "transcribing", "retrieving", "thinking"):
            self._dot_timer.start(400)
        else:
            self._dot_timer.stop()
        
        self.update()
    
    def _update_dots(self):
        """Animate the loading dots."""
        self._dot_count = (self._dot_count + 1) % 4
        dots = "." * self._dot_count
        
        text = self.STATE_TEXT.get(self._state, self._state.title())
        self._label.setText(f"{text}{dots}")


class PulsingDots(QWidget):
    """
    Animated pulsing dots indicator for loading states.
    """
    
    def __init__(self, parent=None, dot_count: int = 3):
        super().__init__(parent)
        
        self._dots = dot_count
        self._current = 0
        
        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Create dot labels
        self._dot_labels = []
        for i in range(dot_count):
            dot = QLabel("●")
            dot.setStyleSheet("font-size: 12px; color: #484F58;")
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(dot)
            self._dot_labels.append(dot)
        
        # Animation timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
    
    def start(self, color: str = "#4B9EFF"):
        """Start the pulsing animation."""
        self._color = color
        self._current = 0
        self._timer.start(300)
    
    def stop(self):
        """Stop the animation."""
        self._timer.stop()
        for dot in self._dot_labels:
            dot.setStyleSheet("font-size: 12px; color: #484F58;")
    
    def _animate(self):
        """Update the dot colors."""
        for i, dot in enumerate(self._dot_labels):
            if i == self._current:
                dot.setStyleSheet(f"font-size: 14px; color: {self._color};")
            else:
                dot.setStyleSheet("font-size: 12px; color: #484F58;")
        
        self._current = (self._current + 1) % len(self._dot_labels)
