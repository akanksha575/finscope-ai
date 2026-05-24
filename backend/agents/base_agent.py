from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
import os
from utils.logger import log

class BaseAgent(ABC):
    """Base class for all FinScope AI agents"""
    
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.3):
        """
        Initialize base agent
        
        Args:
            model: OpenAI model to use
            temperature: Temperature for generation
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        log.info(f"Initialized {self.__class__.__name__} with model {model}")
    
    @abstractmethod
    async def process(self, *args, **kwargs) -> Dict[str, Any]:
        """Process input and return result"""
        pass
    
    async def _call_llm(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """
        Call OpenAI LLM asynchronously
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters
            
        Returns:
            LLM response text
        """
        # Standard chat.completions.create for all models
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                **kwargs
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            log.error(f"LLM call failed: {e}")
            raise