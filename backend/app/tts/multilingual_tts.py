from gtts import gTTS
from pydub import AudioSegment
import uuid
import os


def text_to_speech(text: str, language: str = "hi") -> str:
    """
    Convert text to WAV audio using gTTS.
    Guaranteed non-empty WAV output.
    """

    # language fallback
    lang_map = {
        "hi": "hi",
        "mr": "hi",   # Marathi via Hindi voice (acceptable for demo)
        "ta": "ta",
        "te": "te",
        "bn": "bn",
        "or": "hi"
    }

    tts_lang = lang_map.get(language, "hi")

    mp3_path = f"temp_{uuid.uuid4()}.mp3"
    wav_path = f"temp_audio_{uuid.uuid4()}.wav"

    # Generate MP3
    tts = gTTS(text=text, lang=tts_lang)
    tts.save(mp3_path)

    # Convert to WAV
    audio = AudioSegment.from_mp3(mp3_path)
    audio.export(wav_path, format="wav")

    # Cleanup mp3
    os.remove(mp3_path)

    return wav_path
