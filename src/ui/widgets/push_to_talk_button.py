"""
Push-to-Talk Button Widget with pulsing animation.

A large, circular button that pulses when active and provides
visual feedback for different states.
"""

from PySide6.QtWidgets import QPushButton, QGraphicsDropShadowEffect
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, Property, 
    QSequentialAnimationGroup, Signal, QSize
)
from PySide6.QtGui import QColor, QPainter, QBrush, QRadialGradient, QPen


class PushToTalkButton(QPushButton):
    """
    A circular push-to-talk button with animations.
    
    Features:
    - Pulsing glow animation when listening
    - Color transitions for different states
    - Microphone icon display
    
    Signals:
        recording_started: Emitted when recording begins
        recording_stopped: Emitted when recording ends
    """
    
    recording_started = Signal()
    recording_stopped = Signal()
    
    # State colors
    COLORS = {
        "idle": QColor("#4B9EFF"),
        "listening": QColor("#56D364"),
        "thinking": QColor("#D29922"),
        "speaking": QColor("#8B5CF6"),
        "error": QColor("#F85149"),
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("pttButton")
        
        # Button size
        self.setFixedSize(180, 180)
        self.setCursor(Qt.PointingHandCursor)
        
        # Current state
        self._state = "idle"
        self._pulse_scale = 1.0
        self._glow_opacity = 0.0
        
        # Setup animations
        self._setup_animations()
        
        # Setup shadow effect
        self._setup_shadow()
        
        # Set text
        self.setText("🎤")
        
    def _setup_shadow(self):
        """Add a drop shadow for depth."""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 8)
        self.setGraphicsEffect(shadow)
    
    def _setup_animations(self):
        """Setup the pulsing animation."""
        # Pulse animation for the glow
        self._pulse_animation = QPropertyAnimation(self, b"pulseScale")
        self._pulse_animation.setDuration(1000)
        self._pulse_animation.setStartValue(1.0)
        self._pulse_animation.setKeyValueAt(0.5, 1.15)
        self._pulse_animation.setEndValue(1.0)
        self._pulse_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._pulse_animation.setLoopCount(-1)  # Infinite loop
        
        # Glow opacity animation
        self._glow_animation = QPropertyAnimation(self, b"glowOpacity")
        self._glow_animation.setDuration(500)
        self._glow_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    # Properties for animation
    def _get_pulse_scale(self):
        return self._pulse_scale
    
    def _set_pulse_scale(self, value):
        self._pulse_scale = value
        self.update()
    
    pulseScale = Property(float, _get_pulse_scale, _set_pulse_scale)
    
    def _get_glow_opacity(self):
        return self._glow_opacity
    
    def _set_glow_opacity(self, value):
        self._glow_opacity = value
        self.update()
    
    glowOpacity = Property(float, _get_glow_opacity, _set_glow_opacity)
    
    @property
    def state(self):
        return self._state
    
    def set_state(self, state: str):
        """
        Set the button state.
        
        Args:
            state: One of 'idle', 'listening', 'thinking', 'speaking', 'error'
        """
        if state == self._state:
            return
            
        old_state = self._state
        self._state = state
        
        # Update visual state
        self.setProperty("state", state)
        self.style().unpolish(self)
        self.style().polish(self)
        
        # Start/stop animations
        if state == "listening":
            self._pulse_animation.start()
            self._glow_animation.setStartValue(self._glow_opacity)
            self._glow_animation.setEndValue(0.6)
            self._glow_animation.start()
            self.recording_started.emit()
        else:
            self._pulse_animation.stop()
            self._pulse_scale = 1.0
            if old_state == "listening":
                self.recording_stopped.emit()
            self._glow_animation.setStartValue(self._glow_opacity)
            self._glow_animation.setEndValue(0.0)
            self._glow_animation.start()
        
        # Update button text based on state
        if state == "idle":
            self.setText("🎤")
            self.setEnabled(True)
        elif state == "listening":
            self.setText("🔴")
        elif state == "thinking":
            self.setText("💭")
            self.setEnabled(False)
        elif state == "speaking":
            self.setText("🔊")
            self.setEnabled(False)
        elif state == "error":
            self.setText("⚠️")
            self.setEnabled(True)
        
        self.update()
    
    def paintEvent(self, event):
        """Custom paint for glow effect."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw glow effect when active
        if self._glow_opacity > 0 and self._state in self.COLORS:
            color = self.COLORS[self._state]
            glow_color = QColor(color)
            glow_color.setAlphaF(self._glow_opacity * 0.5)
            
            # Draw pulsing glow
            center = self.rect().center()
            glow_size = int(self.width() * self._pulse_scale * 0.6)
            
            gradient = QRadialGradient(center.x(), center.y(), glow_size)
            gradient.setColorAt(0, glow_color)
            gradient.setColorAt(1, QColor(0, 0, 0, 0))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                center.x() - glow_size,
                center.y() - glow_size,
                glow_size * 2,
                glow_size * 2
            )
        
        painter.end()
        
        # Call parent paint for the button itself
        super().paintEvent(event)
    
    def sizeHint(self):
        return QSize(180, 180)
