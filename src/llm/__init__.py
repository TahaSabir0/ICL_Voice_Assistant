"""
LLM module using Ollama with Llama 3.1.

This module provides:
- LLMClient: Main client for generating responses
- LLMResponse: Result object with text and metadata
- Prompt templates for ICL assistant
"""

from .ollama import (
    LLMClient,
    LLMConfig,
    LLMResponse,
    create_llm_client,
    DEFAULT_SYSTEM_PROMPT,
)

from .prompts import (
    ICL_SYSTEM_PROMPT,
    RAG_SYSTEM_PROMPT,
    NO_CONTEXT_PROMPT,
    format_rag_prompt,
    get_system_prompt,
)

__all__ = [
    # Client
    "LLMClient",
    "LLMConfig",
    "LLMResponse",
    "create_llm_client",
    # Prompts
    "DEFAULT_SYSTEM_PROMPT",
    "ICL_SYSTEM_PROMPT",
    "RAG_SYSTEM_PROMPT",
    "NO_CONTEXT_PROMPT",
    "format_rag_prompt",
    "get_system_prompt",
]
