"""
Groq API integration for LLM capabilities.
Uses Llama 3.3 70B model for Hindi language processing.
"""

import json
from typing import Optional, List, Dict, Any, Generator
from pathlib import Path
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from groq import Groq

import sys
sys.path.append(str(Path(__file__).parent.parent))
from app.config import settings


class GroqClient:
    """Groq API client for LLM interactions."""
    
    def __init__(self):
        """Initialize the Groq client."""
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = settings.groq_model
        self.max_tokens = settings.groq_max_tokens
        self.temperature = settings.groq_temperature
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict] = None
    ) -> str:
        """
        Send a chat completion request.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max tokens
            response_format: Optional JSON response format
            
        Returns:
            Assistant's response text
        """
        logger.debug(f"Sending chat request with {len(messages)} messages")
        
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
        }
        
        if response_format:
            kwargs["response_format"] = response_format
        
        response = self.client.chat.completions.create(**kwargs)
        
        result = response.choices[0].message.content
        logger.debug(f"Received response: {result[:100]}...")
        
        return result
    
    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Send a chat request expecting JSON response.
        
        Args:
            messages: List of message dicts
            temperature: Override default temperature
            
        Returns:
            Parsed JSON response
        """
        response = self.chat(
            messages,
            temperature=temperature,
            response_format={"type": "json_object"}
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response was: {response}")
            raise
    
    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None
    ) -> Generator[str, None, None]:
        """
        Send a streaming chat request.
        
        Args:
            messages: List of message dicts
            temperature: Override default temperature
            
        Yields:
            Response text chunks
        """
        logger.debug(f"Sending streaming chat request with {len(messages)} messages")
        
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=self.max_tokens,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


# Singleton instance
groq_client = GroqClient()


def get_completion(
    system_prompt: str,
    user_message: str,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> str:
    """
    Convenience function for getting a completion.
    
    Args:
        system_prompt: System instructions
        user_message: User's message
        conversation_history: Optional previous conversation turns
        
    Returns:
        Assistant's response
    """
    messages = [{"role": "system", "content": system_prompt}]
    
    if conversation_history:
        messages.extend(conversation_history)
    
    messages.append({"role": "user", "content": user_message})
    
    return groq_client.chat(messages)


def get_json_completion(
    system_prompt: str,
    user_message: str,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Convenience function for getting a JSON completion.
    
    Args:
        system_prompt: System instructions
        user_message: User's message
        conversation_history: Optional previous conversation turns
        
    Returns:
        Parsed JSON response
    """
    messages = [{"role": "system", "content": system_prompt}]
    
    if conversation_history:
        messages.extend(conversation_history)
    
    messages.append({"role": "user", "content": user_message})
    
    return groq_client.chat_json(messages)
