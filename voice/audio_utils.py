"""
Audio utilities for recording and playback.
Handles microphone input and speaker output.
"""

import io
import wave
import tempfile
from pathlib import Path
from typing import Optional, Tuple
import numpy as np
from loguru import logger

try:
    import sounddevice as sd
    import soundfile as sf
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    logger.warning("Audio libraries not available. Voice recording disabled.")


class AudioRecorder:
    """Audio recording utility using sounddevice."""
    
    DEFAULT_SAMPLE_RATE = 16000
    DEFAULT_CHANNELS = 1
    DEFAULT_DTYPE = 'int16'
    
    def __init__(
        self,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        channels: int = DEFAULT_CHANNELS
    ):
        """Initialize the audio recorder."""
        self.sample_rate = sample_rate
        self.channels = channels
        self.recording = False
        self._audio_data = []
        
    def start_recording(self) -> None:
        """Start recording audio from microphone."""
        if not AUDIO_AVAILABLE:
            raise RuntimeError("Audio libraries not available")
        
        self._audio_data = []
        self.recording = True
        logger.info("Started audio recording")
    
    def stop_recording(self) -> np.ndarray:
        """Stop recording and return audio data."""
        self.recording = False
        if self._audio_data:
            audio = np.concatenate(self._audio_data)
        else:
            audio = np.array([], dtype=self.DEFAULT_DTYPE)
        logger.info(f"Stopped recording. Duration: {len(audio) / self.sample_rate:.2f}s")
        return audio
    
    def record_for_duration(self, duration_seconds: float) -> np.ndarray:
        """
        Record audio for a specific duration.
        
        Args:
            duration_seconds: How long to record
            
        Returns:
            NumPy array of audio samples
        """
        if not AUDIO_AVAILABLE:
            raise RuntimeError("Audio libraries not available")
        
        logger.info(f"Recording for {duration_seconds} seconds...")
        
        audio = sd.rec(
            int(duration_seconds * self.sample_rate),
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=self.DEFAULT_DTYPE
        )
        sd.wait()
        
        logger.info(f"Recording complete. Shape: {audio.shape}")
        return audio.flatten()
    
    def record_until_silence(
        self,
        silence_threshold: float = 0.02,
        silence_duration: float = 1.5,
        max_duration: float = 30.0
    ) -> np.ndarray:
        """
        Record until silence is detected.
        
        Args:
            silence_threshold: RMS threshold for silence detection
            silence_duration: How long silence must persist to stop
            max_duration: Maximum recording duration
            
        Returns:
            NumPy array of audio samples
        """
        if not AUDIO_AVAILABLE:
            raise RuntimeError("Audio libraries not available")
        
        logger.info("Recording until silence detected...")
        
        block_size = int(0.1 * self.sample_rate)  # 100ms blocks
        audio_chunks = []
        silence_blocks = 0
        required_silence_blocks = int(silence_duration / 0.1)
        max_blocks = int(max_duration / 0.1)
        
        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=self.DEFAULT_DTYPE,
            blocksize=block_size
        ) as stream:
            for _ in range(max_blocks):
                data, _ = stream.read(block_size)
                audio_chunks.append(data.flatten())
                
                # Calculate RMS
                rms = np.sqrt(np.mean(data.astype(float) ** 2)) / 32768.0
                
                if rms < silence_threshold:
                    silence_blocks += 1
                    if silence_blocks >= required_silence_blocks:
                        logger.info("Silence detected, stopping recording")
                        break
                else:
                    silence_blocks = 0
        
        audio = np.concatenate(audio_chunks)
        logger.info(f"Recording complete. Duration: {len(audio) / self.sample_rate:.2f}s")
        return audio


class AudioPlayer:
    """Audio playback utility."""
    
    def __init__(self, sample_rate: int = 16000):
        """Initialize the audio player."""
        self.sample_rate = sample_rate
    
    def play_audio(self, audio_data: np.ndarray) -> None:
        """
        Play audio from NumPy array.
        
        Args:
            audio_data: Audio samples as NumPy array
        """
        if not AUDIO_AVAILABLE:
            raise RuntimeError("Audio libraries not available")
        
        logger.info(f"Playing audio ({len(audio_data) / self.sample_rate:.2f}s)")
        sd.play(audio_data, self.sample_rate)
        sd.wait()
    
    def play_bytes(self, audio_bytes: bytes) -> None:
        """
        Play audio from bytes (WAV format).
        
        Args:
            audio_bytes: WAV audio bytes
        """
        if not AUDIO_AVAILABLE:
            raise RuntimeError("Audio libraries not available")
        
        # Write to temp file and read back
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            temp_path = f.name
        
        try:
            audio, sr = sf.read(temp_path)
            logger.info(f"Playing audio ({len(audio) / sr:.2f}s)")
            sd.play(audio, sr)
            sd.wait()
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def play_file(self, file_path: str) -> None:
        """
        Play audio from file.
        
        Args:
            file_path: Path to audio file
        """
        if not AUDIO_AVAILABLE:
            raise RuntimeError("Audio libraries not available")
        
        audio, sr = sf.read(file_path)
        logger.info(f"Playing audio file: {file_path} ({len(audio) / sr:.2f}s)")
        sd.play(audio, sr)
        sd.wait()


def save_audio_to_wav(
    audio_data: np.ndarray,
    output_path: str,
    sample_rate: int = 16000
) -> str:
    """
    Save audio data to WAV file.
    
    Args:
        audio_data: Audio samples as NumPy array
        output_path: Path to save WAV file
        sample_rate: Sample rate
        
    Returns:
        Path to saved file
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    sf.write(output_path, audio_data, sample_rate)
    logger.info(f"Audio saved to: {output_path}")
    return output_path


def load_audio_from_file(file_path: str) -> Tuple[np.ndarray, int]:
    """
    Load audio from file.
    
    Args:
        file_path: Path to audio file
        
    Returns:
        Tuple of (audio_data, sample_rate)
    """
    audio, sr = sf.read(file_path)
    return audio, sr


def audio_to_bytes(audio_data: np.ndarray, sample_rate: int = 16000) -> bytes:
    """
    Convert NumPy audio array to WAV bytes.
    
    Args:
        audio_data: Audio samples
        sample_rate: Sample rate
        
    Returns:
        WAV file bytes
    """
    buffer = io.BytesIO()
    sf.write(buffer, audio_data, sample_rate, format='WAV')
    buffer.seek(0)
    return buffer.read()


# Singleton instances
recorder = AudioRecorder()
player = AudioPlayer()
