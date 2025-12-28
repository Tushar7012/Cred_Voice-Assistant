"""
Sarvam AI Text-to-Speech (TTS) Integration.
Uses Sarvam's Bulbul model for Hindi speech synthesis.
"""

import base64
import requests
from typing import Optional
from pathlib import Path
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

import sys
sys.path.append(str(Path(__file__).parent.parent))
from app.config import settings
from app.models import TTSResult


class SarvamTTS:
    """Sarvam AI Text-to-Speech client."""
    
    # Available speakers for Hindi
    SPEAKERS = {
        "meera": "Female, calm and professional",
        "pavithra": "Female, energetic",
        "maitreyi": "Female, warm",
        "arvind": "Male, professional",
        "karthik": "Male, energetic",
    }
    
    def __init__(self):
        """Initialize the TTS client."""
        self.api_key = settings.sarvam_api_key
        self.base_url = settings.sarvam_base_url
        self.model = settings.sarvam_tts_model
        self.speaker = settings.sarvam_tts_speaker
        self.language_code = settings.default_language
        
    def _get_headers(self) -> dict:
        """Get API request headers."""
        return {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json"
        }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def synthesize(
        self,
        text: str,
        speaker: Optional[str] = None,
        enable_preprocessing: bool = True
    ) -> TTSResult:
        """
        Convert text to speech.
        
        Args:
            text: Hindi text to synthesize
            speaker: Speaker voice to use (default from settings)
            enable_preprocessing: Whether to normalize numbers, dates, etc.
            
        Returns:
            TTSResult with audio data
        """
        logger.info(f"Synthesizing speech for text ({len(text)} chars)")
        
        url = f"{self.base_url}/text-to-speech"
        
        payload = {
            "inputs": [text],
            "target_language_code": self.language_code,
            "speaker": speaker or self.speaker,
            "model": self.model,
            "enable_preprocessing": enable_preprocessing
        }
        
        response = requests.post(
            url,
            headers=self._get_headers(),
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            logger.error(f"TTS API error: {response.status_code} - {response.text}")
            raise Exception(f"TTS API error: {response.status_code} - {response.text}")
        
        result = response.json()
        
        # Decode base64 audio
        audio_base64 = result.get("audios", [None])[0]
        if not audio_base64:
            raise Exception("No audio data received from TTS API")
        
        audio_bytes = base64.b64decode(audio_base64)
        
        logger.info(f"Speech synthesis complete ({len(audio_bytes)} bytes)")
        
        return TTSResult(
            audio_data=audio_bytes,
            audio_format="wav",
            duration_seconds=len(audio_bytes) / (16000 * 2),  # Approximate
            text_length=len(text)
        )
    
    def synthesize_to_file(
        self,
        text: str,
        output_path: str,
        speaker: Optional[str] = None
    ) -> str:
        """
        Convert text to speech and save to file.
        
        Args:
            text: Hindi text to synthesize
            output_path: Path to save the audio file
            speaker: Speaker voice to use
            
        Returns:
            Path to the saved audio file
        """
        result = self.synthesize(text, speaker)
        
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output, "wb") as f:
            f.write(result.audio_data)
        
        logger.info(f"Audio saved to: {output_path}")
        return str(output)


# Singleton instance
tts_client = SarvamTTS()


def text_to_speech(text: str, output_path: Optional[str] = None) -> bytes:
    """
    Convenience function to convert text to speech.
    
    Args:
        text: Hindi text to synthesize
        output_path: Optional path to save audio file
        
    Returns:
        Audio bytes
    """
    result = tts_client.synthesize(text)
    
    if output_path:
        with open(output_path, "wb") as f:
            f.write(result.audio_data)
    
    return result.audio_data


def get_available_speakers() -> dict:
    """Get available speaker voices."""
    return SarvamTTS.SPEAKERS
