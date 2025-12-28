"""
Configuration management for the Voice Assistant application.
Uses Pydantic Settings for environment variable management.
"""

import os
from typing import Literal
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    sarvam_api_key: str = Field(
        default="",
        description="Sarvam AI API key for STT/TTS"
    )
    groq_api_key: str = Field(
        default="",
        description="Groq API key for LLM"
    )
    
    # Language Settings
    default_language: str = Field(
        default="hi-IN",
        description="Default language code (hi-IN for Hindi)"
    )
    
    # Sarvam AI Settings
    sarvam_stt_model: str = Field(
        default="saarika:v1",
        description="Sarvam STT model name"
    )
    sarvam_tts_model: str = Field(
        default="bulbul:v2",
        description="Sarvam TTS model name"
    )
    sarvam_tts_speaker: str = Field(
        default="anushka",
        description="Sarvam TTS speaker voice"
    )
    sarvam_base_url: str = Field(
        default="https://api.sarvam.ai",
        description="Sarvam AI API base URL"
    )
    
    # Groq Settings
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        description="Groq LLM model name"
    )
    groq_max_tokens: int = Field(
        default=2048,
        description="Maximum tokens for LLM response"
    )
    groq_temperature: float = Field(
        default=0.7,
        description="LLM temperature for response generation"
    )
    
    # Memory Settings
    max_conversation_turns: int = Field(
        default=10,
        description="Maximum conversation turns to keep in memory"
    )
    
    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    # ChromaDB Settings
    chroma_persist_directory: str = Field(
        default="data/chroma_db",
        description="Directory for ChromaDB persistence"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def validate_settings() -> bool:
    """Validate that required settings are configured."""
    errors = []
    
    if not settings.sarvam_api_key:
        errors.append("SARVAM_API_KEY is not set")
    
    if not settings.groq_api_key:
        errors.append("GROQ_API_KEY is not set")
    
    if errors:
        for error in errors:
            print(f"Configuration Error: {error}")
        return False
    
    return True
