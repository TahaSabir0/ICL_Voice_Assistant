"""
Tests for voice pipeline.
"""

import pytest


def test_pipeline_config_defaults():
    """Test PipelineConfig has correct defaults."""
    from src.pipeline import PipelineConfig
    
    config = PipelineConfig()
    assert config.stt_model == "base"
    assert config.llm_model == "llama3.1:8b-instruct-q4_K_M"
    assert config.llm_max_tokens == 256


def test_pipeline_initialization():
    """Test VoicePipeline can be created."""
    from src.pipeline import VoicePipeline
    
    pipeline = VoicePipeline()
    assert not pipeline.is_initialized
    assert len(pipeline.conversation_history) == 0


def test_pipeline_state_enum():
    """Test PipelineState enum values."""
    from src.pipeline import PipelineState
    
    assert PipelineState.IDLE.value == "idle"
    assert PipelineState.LISTENING.value == "listening"
    assert PipelineState.TRANSCRIBING.value == "transcribing"
    assert PipelineState.THINKING.value == "thinking"
    assert PipelineState.SPEAKING.value == "speaking"


def test_pipeline_metrics():
    """Test PipelineMetrics calculations."""
    from src.pipeline import PipelineMetrics
    
    metrics = PipelineMetrics(
        recording_duration=2.0,
        stt_time=1.0,
        llm_time=3.0,
        tts_time=0.5,
        playback_duration=2.5
    )
    
    assert metrics.total_processing_time == 4.5  # 1 + 3 + 0.5
    assert metrics.end_to_end_time == 9.0  # 2 + 1 + 3 + 0.5 + 2.5


def test_pipeline_metrics_to_dict():
    """Test PipelineMetrics.to_dict()."""
    from src.pipeline import PipelineMetrics
    
    metrics = PipelineMetrics(
        stt_time=1.0,
        llm_time=2.0,
        tts_time=0.5
    )
    
    d = metrics.to_dict()
    assert d["stt"] == 1.0
    assert d["llm"] == 2.0
    assert d["tts"] == 0.5
    assert d["processing"] == 3.5


def test_conversation_turn():
    """Test ConversationTurn dataclass."""
    from src.pipeline import ConversationTurn, PipelineMetrics
    
    metrics = PipelineMetrics(llm_time=2.0)
    turn = ConversationTurn(
        user_audio_duration=3.0,
        user_text="Hello",
        assistant_text="Hi there!",
        assistant_audio_duration=1.5,
        metrics=metrics
    )
    
    assert turn.user_text == "Hello"
    assert turn.assistant_text == "Hi there!"
    assert turn.timestamp > 0


def test_pipeline_full_initialization():
    """Test full pipeline initialization (all components load)."""
    from src.pipeline import VoicePipeline, PipelineConfig
    
    config = PipelineConfig(
        stt_model="tiny",  # Use tiny for faster test
        stt_device="cpu",
    )
    pipeline = VoicePipeline(config)
    
    success = pipeline.initialize()
    
    assert success
    assert pipeline.is_initialized
    
    # Cleanup
    pipeline.shutdown()
    assert not pipeline.is_initialized


def test_pipeline_process_text():
    """Test processing text input (skips audio recording)."""
    from src.pipeline import VoicePipeline, PipelineConfig
    
    config = PipelineConfig(
        stt_model="tiny",
        stt_device="cpu",
        llm_max_tokens=50,  # Short response for fast test
    )
    pipeline = VoicePipeline(config)
    pipeline.initialize()
    
    result = pipeline.process_text("Hello, how are you?")
    
    assert result is not None
    assert result.user_text == "Hello, how are you?"
    assert len(result.assistant_text) > 0
    assert result.metrics.llm_time > 0
    assert result.metrics.tts_time > 0
    
    # Check history
    assert len(pipeline.conversation_history) == 1
    
    # Cleanup
    pipeline.shutdown()
