"""
Styles and themes for the ICL Voice Assistant Kiosk UI.

Modern, polished design with dark mode and vibrant accent colors.
"""

# Color palette - Modern dark theme with vibrant accents
COLORS = {
    # Base colors
    "background": "#0D1117",          # Deep dark background
    "surface": "#161B22",             # Elevated surfaces
    "surface_elevated": "#21262D",    # Cards, panels
    
    # Text colors
    "text_primary": "#F0F6FC",        # Primary text - high contrast
    "text_secondary": "#8B949E",      # Secondary text - muted
    "text_muted": "#484F58",          # Disabled/hint text
    
    # Accent colors - ICL brand inspired
    "accent_primary": "#4B9EFF",      # Primary accent - vibrant blue
    "accent_secondary": "#79C0FF",    # Lighter accent
    "accent_glow": "rgba(75, 158, 255, 0.3)",  # Glow effect
    
    # State colors
    "idle": "#4B9EFF",                # Blue - ready state
    "listening": "#56D364",           # Green - recording
    "listening_glow": "rgba(86, 211, 100, 0.4)",
    "thinking": "#D29922",            # Amber - processing
    "thinking_glow": "rgba(210, 153, 34, 0.4)",
    "speaking": "#8B5CF6",            # Purple - speaking
    "speaking_glow": "rgba(139, 92, 246, 0.4)",
    "error": "#F85149",               # Red - error state
    
    # Border colors
    "border": "#30363D",
    "border_hover": "#484F58",
}

# Typography
FONTS = {
    "family": "Inter, Segoe UI, sans-serif",
    "family_mono": "JetBrains Mono, Consolas, monospace",
    "size_xl": "48px",
    "size_lg": "24px",
    "size_md": "18px",
    "size_sm": "14px",
    "size_xs": "12px",
    "weight_normal": "400",
    "weight_medium": "500",
    "weight_semibold": "600",
    "weight_bold": "700",
}

# Main stylesheet for the kiosk application
MAIN_STYLESHEET = f"""
/* Global styles */
* {{
    font-family: {FONTS['family']};
    color: {COLORS['text_primary']};
}}

QMainWindow {{
    background-color: {COLORS['background']};
}}

QWidget {{
    background-color: transparent;
}}

/* Main container */
#mainContainer {{
    background-color: {COLORS['background']};
}}

/* Header section */
#headerLabel {{
    color: {COLORS['text_primary']};
    font-size: {FONTS['size_lg']};
    font-weight: {FONTS['weight_bold']};
    padding: 20px;
}}

/* State indicator */
#stateLabel {{
    color: {COLORS['text_secondary']};
    font-size: {FONTS['size_md']};
    font-weight: {FONTS['weight_medium']};
    padding: 10px 20px;
    border-radius: 8px;
    background-color: {COLORS['surface']};
}}

#stateLabel[state="idle"] {{
    color: {COLORS['idle']};
    border: 2px solid {COLORS['idle']};
}}

#stateLabel[state="listening"] {{
    color: {COLORS['listening']};
    border: 2px solid {COLORS['listening']};
    background-color: rgba(86, 211, 100, 0.1);
}}

#stateLabel[state="thinking"] {{
    color: {COLORS['thinking']};
    border: 2px solid {COLORS['thinking']};
    background-color: rgba(210, 153, 34, 0.1);
}}

#stateLabel[state="speaking"] {{
    color: {COLORS['speaking']};
    border: 2px solid {COLORS['speaking']};
    background-color: rgba(139, 92, 246, 0.1);
}}

#stateLabel[state="error"] {{
    color: {COLORS['error']};
    border: 2px solid {COLORS['error']};
    background-color: rgba(248, 81, 73, 0.1);
}}

/* Push to talk button */
#pttButton {{
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 {COLORS['accent_primary']},
        stop:1 #3B8AE8
    );
    color: white;
    font-size: {FONTS['size_lg']};
    font-weight: {FONTS['weight_bold']};
    border: none;
    border-radius: 50%;
    min-width: 180px;
    min-height: 180px;
    max-width: 180px;
    max-height: 180px;
}}

#pttButton:hover {{
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 {COLORS['accent_secondary']},
        stop:1 {COLORS['accent_primary']}
    );
}}

#pttButton:pressed {{
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #3B8AE8,
        stop:1 #2A6BC0
    );
}}

#pttButton:disabled {{
    background: {COLORS['surface_elevated']};
    color: {COLORS['text_muted']};
}}

#pttButton[state="listening"] {{
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 {COLORS['listening']},
        stop:1 #42A552
    );
}}

/* Conversation panel */
#conversationPanel {{
    background-color: {COLORS['surface']};
    border-radius: 16px;
    border: 1px solid {COLORS['border']};
    padding: 20px;
}}

/* Message bubbles */
#userBubble {{
    background-color: {COLORS['surface_elevated']};
    border-radius: 16px;
    border-bottom-right-radius: 4px;
    padding: 16px 20px;
    margin: 8px 0;
}}

#assistantBubble {{
    background-color: {COLORS['accent_primary']};
    color: white;
    border-radius: 16px;
    border-bottom-left-radius: 4px;
    padding: 16px 20px;
    margin: 8px 0;
}}

#userLabel {{
    color: {COLORS['text_secondary']};
    font-size: {FONTS['size_sm']};
    font-weight: {FONTS['weight_medium']};
}}

#messageText {{
    color: {COLORS['text_primary']};
    font-size: {FONTS['size_md']};
    line-height: 1.5;
}}

#assistantBubble #messageText {{
    color: white;
}}

/* Scroll area */
QScrollArea {{
    border: none;
    background-color: transparent;
}}

QScrollBar:vertical {{
    background: {COLORS['surface']};
    width: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background: {COLORS['border_hover']};
    border-radius: 4px;
    min-height: 40px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS['text_muted']};
}}

QScrollBar::add-line:vertical, 
QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* Status bar */
#statusBar {{
    background-color: {COLORS['surface']};
    padding: 8px 16px;
    font-size: {FONTS['size_sm']};
    color: {COLORS['text_secondary']};
}}

/* Loading animation placeholder */
#loadingDots {{
    font-size: {FONTS['size_xl']};
    color: {COLORS['accent_primary']};
}}
"""

# State-specific button styles
BUTTON_STYLES = {
    "idle": f"""
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 {COLORS['accent_primary']},
            stop:1 #3B8AE8
        );
    """,
    "listening": f"""
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 {COLORS['listening']},
            stop:1 #42A552
        );
    """,
    "thinking": f"""
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 {COLORS['thinking']},
            stop:1 #B8820F
        );
    """,
    "speaking": f"""
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 {COLORS['speaking']},
            stop:1 #7048D5
        );
    """,
    "disabled": f"""
        background: {COLORS['surface_elevated']};
        color: {COLORS['text_muted']};
    """,
}
