"""
Ollama LLM client for ICL Voice Assistant.

Provides a wrapper around the Ollama Python client for
generating responses using local LLM models.
"""

import time
from dataclasses import dataclass
from typing import Optional, List, Generator
import ollama


@dataclass
class LLMConfig:
    """Configuration for the LLM client."""
    model: str = "llama3.1:8b-instruct-q4_K_M"
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 512
    system_prompt: Optional[str] = None


@dataclass
class LLMResponse:
    """Result of an LLM generation."""
    text: str
    model: str
    processing_time: float  # Time taken to generate
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    
    @property
    def tokens_per_second(self) -> float:
        """Generation speed in tokens per second."""
        if self.completion_tokens and self.processing_time > 0:
            return self.completion_tokens / self.processing_time
        return 0


# Default system prompt for ICL assistant
DEFAULT_SYSTEM_PROMPT = """You are a helpful voice assistant for the Innovation & Creativity Lab (ICL) at Gettysburg College. 

The ICL is a makerspace with equipment including:
- 3D printers (FDM and resin)
- Laser cutters
- CNC machines
- Vinyl cutters
- Sewing and embroidery machines
- Sublimation printing
- Virtual reality systems

You help students and staff with:
- How to use equipment
- Safety guidelines
- Project recommendations
- Troubleshooting common issues

Keep your responses concise and conversational since they will be spoken aloud.
If you don't know something, say so honestly."""


class LLMClient:
    """
    LLM client using Ollama for local inference.
    
    Usage:
        llm = LLMClient()
        
        response = llm.generate("How do I use the 3D printer?")
        print(response.text)
        
        # Or stream the response
        for chunk in llm.generate_stream("Tell me about laser cutting"):
            print(chunk, end="", flush=True)
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self._client = ollama
        self._is_available = False
        
        # Set default system prompt
        if self.config.system_prompt is None:
            self.config.system_prompt = DEFAULT_SYSTEM_PROMPT
    
    @property
    def is_available(self) -> bool:
        """Whether the LLM is available."""
        return self._is_available
    
    def check_availability(self) -> bool:
        """
        Check if Ollama is running and the model is available.
        
        Returns:
            True if available.
        """
        try:
            models = self._client.list()
            model_names = [m.model for m in models.models]
            
            # Check if our model is available
            model_available = any(
                self.config.model in name or name in self.config.model
                for name in model_names
            )
            
            self._is_available = model_available
            return model_available
            
        except Exception as e:
            print(f"Ollama not available: {e}")
            self._is_available = False
            return False
    
    def generate(
        self,
        prompt: str,
        context: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: User's question or prompt.
            context: Optional context to include (e.g., from RAG).
            system_prompt: Optional override for system prompt.
            
        Returns:
            LLMResponse with generated text and metadata.
        """
        # Build messages
        messages = []
        
        # System prompt
        sys_prompt = system_prompt or self.config.system_prompt
        if sys_prompt:
            full_system = sys_prompt
            if context:
                full_system += f"\n\nRelevant context:\n{context}"
            messages.append({"role": "system", "content": full_system})
        
        # User message
        messages.append({"role": "user", "content": prompt})
        
        # Generate
        start = time.time()
        
        response = self._client.chat(
            model=self.config.model,
            messages=messages,
            options={
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "num_predict": self.config.max_tokens,
            }
        )
        
        processing_time = time.time() - start
        
        # Extract response text
        text = response.message.content
        
        # Try to get token counts (may not be available)
        prompt_tokens = getattr(response, 'prompt_eval_count', None)
        completion_tokens = getattr(response, 'eval_count', None)
        
        return LLMResponse(
            text=text,
            model=self.config.model,
            processing_time=processing_time,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
    
    def generate_stream(
        self,
        prompt: str,
        context: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> Generator[str, None, None]:
        """
        Generate a streaming response from the LLM.
        
        Args:
            prompt: User's question or prompt.
            context: Optional context to include.
            system_prompt: Optional override for system prompt.
            
        Yields:
            Text chunks as they are generated.
        """
        # Build messages
        messages = []
        
        sys_prompt = system_prompt or self.config.system_prompt
        if sys_prompt:
            full_system = sys_prompt
            if context:
                full_system += f"\n\nRelevant context:\n{context}"
            messages.append({"role": "system", "content": full_system})
        
        messages.append({"role": "user", "content": prompt})
        
        # Stream response
        stream = self._client.chat(
            model=self.config.model,
            messages=messages,
            stream=True,
            options={
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "num_predict": self.config.max_tokens,
            }
        )
        
        for chunk in stream:
            if chunk.message.content:
                yield chunk.message.content
    
    def list_models(self) -> List[str]:
        """List available models."""
        try:
            models = self._client.list()
            return [m.model for m in models.models]
        except Exception:
            return []


def create_llm_client(
    model: str = "llama3.1:8b-instruct-q4_K_M",
    check_availability: bool = True
) -> LLMClient:
    """
    Factory function to create an LLM client.
    
    Args:
        model: Model name to use.
        check_availability: Whether to check if model is available.
        
    Returns:
        Configured LLMClient instance.
    """
    config = LLMConfig(model=model)
    client = LLMClient(config)
    
    if check_availability:
        client.check_availability()
    
    return client
