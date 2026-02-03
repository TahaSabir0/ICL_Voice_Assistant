"""
Conversation View Widget.

Displays the conversation history with user questions and assistant answers
in a scrollable message view similar to a chat interface.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QScrollArea, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor
from typing import Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Message:
    """A single message in the conversation."""
    role: str  # 'user' or 'assistant'
    text: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class MessageBubble(QFrame):
    """
    A single message bubble in the conversation.
    
    User messages appear on the right with a darker background.
    Assistant messages appear on the left with the accent color.
    """
    
    def __init__(self, message: Message, parent=None):
        super().__init__(parent)
        
        self.message = message
        is_user = message.role == "user"
        
        # Set object name for styling
        self.setObjectName("userBubble" if is_user else "assistantBubble")
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # Role label
        role_label = QLabel("You" if is_user else "ICL Assistant")
        role_label.setObjectName("userLabel")
        if not is_user:
            role_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        layout.addWidget(role_label)
        
        # Message text
        text_label = QLabel(message.text)
        text_label.setObjectName("messageText")
        text_label.setWordWrap(True)
        text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(text_label)
        
        # Size policy - expand horizontally but fit content vertically
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        # Apply base styles
        if is_user:
            self.setStyleSheet("""
                MessageBubble {
                    background-color: #21262D;
                    border-radius: 16px;
                    border-bottom-right-radius: 4px;
                }
                #userLabel {
                    color: #8B949E;
                    font-size: 12px;
                    font-weight: 500;
                }
                #messageText {
                    color: #F0F6FC;
                    font-size: 16px;
                }
            """)
        else:
            self.setStyleSheet("""
                MessageBubble {
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 #4B9EFF,
                        stop:1 #3B8AE8
                    );
                    border-radius: 16px;
                    border-bottom-left-radius: 4px;
                }
                #userLabel {
                    color: rgba(255, 255, 255, 0.8);
                    font-size: 12px;
                    font-weight: 500;
                }
                #messageText {
                    color: white;
                    font-size: 16px;
                }
            """)


class ThinkingIndicator(QFrame):
    """
    Animated "thinking" indicator shown while the assistant is processing.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setObjectName("assistantBubble")
        self.setStyleSheet("""
            ThinkingIndicator {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4B9EFF,
                    stop:1 #3B8AE8
                );
                border-radius: 16px;
                border-bottom-left-radius: 4px;
                padding: 16px;
            }
        """)
        
        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(4)
        
        # Dots
        self._dots = []
        for i in range(3):
            dot = QLabel("●")
            dot.setStyleSheet("color: rgba(255, 255, 255, 0.5); font-size: 20px;")
            layout.addWidget(dot)
            self._dots.append(dot)
        
        layout.addStretch()
        
        # Animation
        self._current = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
    
    def start(self):
        """Start the animation."""
        self._timer.start(300)
    
    def stop(self):
        """Stop the animation."""
        self._timer.stop()
    
    def _animate(self):
        """Cycle through dots."""
        for i, dot in enumerate(self._dots):
            if i == self._current:
                dot.setStyleSheet("color: white; font-size: 24px;")
            else:
                dot.setStyleSheet("color: rgba(255, 255, 255, 0.5); font-size: 20px;")
        
        self._current = (self._current + 1) % 3


class ConversationView(QWidget):
    """
    Scrollable conversation view showing all messages.
    
    Features:
    - Auto-scroll to new messages
    - Animated thinking indicator
    - Clear history function
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setObjectName("conversationPanel")
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Scroll area
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        main_layout.addWidget(self._scroll_area)
        
        # Content widget
        self._content = QWidget()
        self._content.setStyleSheet("background: transparent;")
        self._scroll_area.setWidget(self._content)
        
        # Content layout for messages
        self._messages_layout = QVBoxLayout(self._content)
        self._messages_layout.setContentsMargins(20, 20, 20, 20)
        self._messages_layout.setSpacing(16)
        self._messages_layout.addStretch()
        
        # Thinking indicator (hidden by default)
        self._thinking = ThinkingIndicator()
        self._thinking.setVisible(False)
        
        # Placeholder for empty state
        self._placeholder = QLabel("Press the button and ask a question about the ICL!")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet("""
            QLabel {
                color: #8B949E;
                font-size: 18px;
                padding: 40px;
            }
        """)
        self._messages_layout.insertWidget(0, self._placeholder)
        
        # Track messages
        self._messages = []
    
    def add_message(self, role: str, text: str):
        """
        Add a new message to the conversation.
        
        Args:
            role: 'user' or 'assistant'
            text: The message text
        """
        # Hide placeholder on first message
        if self._placeholder.isVisible():
            self._placeholder.setVisible(False)
        
        # Create message
        message = Message(role=role, text=text)
        self._messages.append(message)
        
        # Create bubble
        bubble = MessageBubble(message)
        
        # Insert before the stretch
        insert_index = self._messages_layout.count() - 1  # Before stretch
        self._messages_layout.insertWidget(insert_index, bubble)
        
        # Force visibility and update
        print(f">>> ConversationView: Added {role} message at index {insert_index}, text_len={len(text)}")
        bubble.show()
        bubble.updateGeometry()
        self.updateGeometry()
        
        # Scroll to bottom
        QTimer.singleShot(50, self._scroll_to_bottom)
    
    def show_thinking(self):
        """Show the thinking indicator."""
        if not self._thinking.parent():
            insert_index = self._messages_layout.count() - 1
            self._messages_layout.insertWidget(insert_index, self._thinking)
        
        self._thinking.setVisible(True)
        self._thinking.start()
        
        QTimer.singleShot(50, self._scroll_to_bottom)
    
    def hide_thinking(self):
        """Hide the thinking indicator."""
        self._thinking.stop()
        self._thinking.setVisible(False)
    
    def clear(self):
        """Clear all messages."""
        # Remove all message bubbles
        while self._messages_layout.count() > 1:  # Keep the stretch
            item = self._messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self._messages = []
        
        # Re-add placeholder
        self._placeholder = QLabel("Press the button and ask a question about the ICL!")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet("""
            QLabel {
                color: #8B949E;
                font-size: 18px;
                padding: 40px;
            }
        """)
        self._messages_layout.insertWidget(0, self._placeholder)
    
    def _scroll_to_bottom(self):
        """Scroll to the bottom of the conversation."""
        scrollbar = self._scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
