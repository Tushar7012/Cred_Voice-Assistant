"""
Sarvam AI Speech-to-Text (STT) Integration.
Uses Sarvam's Saarika model for Hindi speech recognition.
"""

import base64
import requests
from typing import Optional, Tuple
from pathlib import Path
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

import sys
sys.path.append(str(Path(__file__).parent.parent))
from app.config import settings
from app.models import STTResult


class SarvamSTT:
    """Sarvam AI Speech-to-Text client."""
    
    def __init__(self):
        """Initialize the STT client."""
        self.api_key = settings.sarvam_api_key
        self.base_url = settings.sarvam_base_url
        self.model = settings.sarvam_stt_model
        self.language_code = settings.default_language
        
    def _get_headers(self) -> dict:
        """Get API request headers."""
        return {
            "api-subscription-key": self.api_key,
        }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def transcribe_file(self, audio_file_path: str) -> STTResult:
        """
        Transcribe audio from a file.
        
        Args:
            audio_file_path: Path to the audio file (WAV, MP3, etc.)
            
        Returns:
            STTResult with transcribed text
        """
        logger.info(f"Transcribing audio file: {audio_file_path}")
        
        # Read and prepare the audio file
        audio_path = Path(audio_file_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        # Prepare the request
        url = f"{self.base_url}/speech-to-text"
        
        with open(audio_path, "rb") as audio_file:
            files = {
                "file": (audio_path.name, audio_file, "audio/wav")
            }
            data = {
                "model": self.model,
                "language_code": self.language_code,
            }
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                files=files,
                data=data,
                timeout=30
            )
        
        if response.status_code != 200:
            logger.error(f"STT API error: {response.status_code} - {response.text}")
            raise Exception(f"STT API error: {response.status_code} - {response.text}")
        
        result = response.json()
        logger.info(f"Transcription result: {result}")
        
        return STTResult(
            text=result.get("transcript", ""),
            language_code=result.get("language_code", self.language_code),
            confidence=result.get("confidence", 0.0),
            audio_duration_seconds=result.get("duration", 0.0)
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def transcribe_bytes(self, audio_bytes: bytes, filename: str = "audio.wav") -> STTResult:
        """
        Transcribe audio from bytes.
        
        Args:
            audio_bytes: Raw audio bytes
            filename: Filename for the audio (determines format)
            
        Returns:
            STTResult with transcribed text
        """
        logger.info(f"Transcribing audio bytes ({len(audio_bytes)} bytes)")
        
        url = f"{self.base_url}/speech-to-text"
        
        files = {
            "file": (filename, audio_bytes, "audio/wav")
        }
        data = {
            "model": self.model,
            "language_code": self.language_code,
        }
        
        response = requests.post(
            url,
            headers=self._get_headers(),
            files=files,
            data=data,
            timeout=30
        )
        
        if response.status_code != 200:
            logger.error(f"STT API error: {response.status_code} - {response.text}")
            raise Exception(f"STT API error: {response.status_code} - {response.text}")
        
        result = response.json()
        logger.info(f"Transcription result: {result}")
        
        return STTResult(
            text=result.get("transcript", ""),
            language_code=result.get("language_code", self.language_code),
            confidence=result.get("confidence", 0.0),
            audio_duration_seconds=result.get("duration", 0.0)
        )


# Singleton instance
stt_client = SarvamSTT()


def transcribe_audio(audio_file_path: str) -> Tuple[str, float]:
    """
    Convenience function to transcribe audio file.
    
    Args:
        audio_file_path: Path to audio file
        
    Returns:
        Tuple of (transcribed_text, confidence_score)
    """
    result = stt_client.transcribe_file(audio_file_path)
    return result.text, result.confidence


def transcribe_audio_bytes(audio_bytes: bytes) -> Tuple[str, float]:
    """
    Convenience function to transcribe audio bytes.
    
    Args:
        audio_bytes: Raw audio bytes
        
    Returns:
        Tuple of (transcribed_text, confidence_score)
    """
    result = stt_client.transcribe_bytes(audio_bytes)
    return result.text, result.confidence
