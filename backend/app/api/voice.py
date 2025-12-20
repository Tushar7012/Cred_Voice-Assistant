import uuid
import os

from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse

from app.stt.whisper_stt import transcribe_audio
from app.agent.agent_loop import run_agent
from app.tts.multilingual_tts import text_to_speech
from app.memory.memory_store import create_session

router = APIRouter()


@router.post("/")
async def voice_agent(
    audio: UploadFile = File(...),
    session_id: str | None = None
):
    """
    Voice-based agent endpoint
    Input  : Audio (wav/mp3)
    Output : Audio (wav)
    """

    # -------------------------------------------------
    # 1. Create or reuse session
    # -------------------------------------------------
    if session_id is None:
        session_id = create_session()

    # -------------------------------------------------
    # 2. Save uploaded audio safely
    # -------------------------------------------------
    input_audio_path = f"temp_input_{uuid.uuid4()}.wav"
    with open(input_audio_path, "wb") as f:
        f.write(await audio.read())

    try:
        # -------------------------------------------------
        # 3. Speech to Text (Whisper)
        # -------------------------------------------------
        text, language, confidence = transcribe_audio(input_audio_path)

        # -------------------------------------------------
        # 4. Low-confidence handling
        # -------------------------------------------------
        if confidence < 0.6 or not text:
            fallback_text = (
                "माफ़ कीजिए, आपकी आवाज़ स्पष्ट नहीं थी। "
                "कृपया फिर से बोलिए।"
            )
            output_audio = text_to_speech(fallback_text, language)

            response = FileResponse(
                output_audio,
                media_type="audio/wav",
                filename="response.wav"
            )
            response.headers["X-Session-ID"] = session_id
            return response

        # -------------------------------------------------
        # 5. Agent reasoning
        # -------------------------------------------------
        response_text = run_agent(
            user_text=text,
            language=language,
            session_id=session_id
        )

        # -------------------------------------------------
        # 6. Text to Speech
        # -------------------------------------------------
        output_audio = text_to_speech(response_text, language)

        # -------------------------------------------------
        # 7. Final response
        # -------------------------------------------------
        response = FileResponse(
            output_audio,
            media_type="audio/wav",
            filename="response.wav"
        )
        response.headers["X-Session-ID"] = session_id
        return response

    finally:
        # -------------------------------------------------
        # 8. Cleanup input audio
        # -------------------------------------------------
        if os.path.exists(input_audio_path):
            os.remove(input_audio_path)
