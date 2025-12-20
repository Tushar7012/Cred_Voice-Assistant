import streamlit as st
import requests
import tempfile
import sounddevice as sd
import scipy.io.wavfile as wav

BACKEND_URL = "http://127.0.0.1:8000/voice/"

st.set_page_config(page_title="Voice Assistant", layout="centered")
st.title("🎙 Voice Assistant")

if "session_id" not in st.session_state:
    st.session_state.session_id = None

st.markdown("### Speak naturally.")

if st.button("🎙 Speak"):
    st.info("Listening...")

    fs = 16000
    duration = 5

    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav.write(tmp.name, fs, recording)

        with open(tmp.name, "rb") as f:
            files = {"audio": ("input.wav", f.read(), "audio/wav")}
            params = {}

            if st.session_state.session_id:
                params["session_id"] = st.session_state.session_id

            with st.spinner("Thinking..."):
                response = requests.post(
                    BACKEND_URL,
                    files=files,
                    params=params,
                    timeout=120
                )

            if response.status_code == 200:
                st.session_state.session_id = response.headers.get("X-Session-ID")

                # 🔥 Auto-play audio (no UI)
                st.audio(response.content, format="audio/wav", autoplay=True)
            else:
                st.error("Assistant could not respond.")
