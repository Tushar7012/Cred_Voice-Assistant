import whisper
import torch


# Force CPU usage (disable CUDA)
torch.cuda.is_available = lambda: False

model = whisper.load_model("base", device="cpu")


def transcribe_audio(audio_path: str):
    result = model.transcribe(audio_path)

    text = result.get("text", "").strip()
    language = result.get("language", "mr")
    confidence = 0.9  # Whisper doesn't expose confidence reliably

    return text, language, confidence
