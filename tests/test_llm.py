"""
Tests for LLM module.
"""

import pytest


def test_llm_config_defaults():
    """Test LLMConfig has correct defaults."""
    from src.llm import LLMConfig
    
    config = LLMConfig()
    assert config.model == "llama3.1:8b-instruct-q4_K_M"
    assert config.temperature == 0.7
    assert config.max_tokens == 512


def test_llm_client_initialization():
    """Test LLMClient can be created."""
    from src.llm import LLMClient
    
    client = LLMClient()
    assert client is not None


def test_llm_check_availability():
    """Test checking LLM availability."""
    from src.llm import LLMClient
    
    client = LLMClient()
    available = client.check_availability()
    
    # Should be available since we pulled the model
    assert available
    assert client.is_available


def test_llm_generate():
    """Test generating a response."""
    from src.llm import LLMClient
    
    client = LLMClient()
    client.check_availability()
    
    response = client.generate("Say 'hello' and nothing else.")
    
    assert response is not None
    assert len(response.text) > 0
    assert response.processing_time > 0


def test_llm_generate_with_context():
    """Test generating with context."""
    from src.llm import LLMClient
    
    client = LLMClient()
    client.check_availability()
    
    context = "The ICL has 3 Prusa 3D printers and 2 Ender printers."
    response = client.generate(
        "How many 3D printers do you have?",
        context=context
    )
    
    assert response is not None
    assert len(response.text) > 0


def test_llm_list_models():
    """Test listing available models."""
    from src.llm import LLMClient
    
    client = LLMClient()
    models = client.list_models()
    
    assert isinstance(models, list)
    assert len(models) > 0
    # Our model should be in the list
    assert any("llama3.1" in m for m in models)


def test_prompt_templates():
    """Test prompt template functions."""
    from src.llm import get_system_prompt, format_rag_prompt
    
    # Without context
    prompt = get_system_prompt(has_context=False)
    assert "ICL" in prompt
    assert "makerspace" in prompt.lower() or "Innovation" in prompt
    
    # With context
    context = "Test context"
    prompt = get_system_prompt(has_context=True, context=context)
    assert "Test context" in prompt
