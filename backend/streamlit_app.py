import streamlit as st
import requests
import tempfile
import sounddevice as sd
import scipy.io.wavfile as wav
import time
import os

BACKEND_URL = "http://127.0.0.1:8000/voice/"
SAMPLE_RATE = 16000

st.set_page_config(page_title="Voice Assistant", layout="centered")
st.title("🎙️ Voice Assistant")

# ---------------------------
# Session state
# ---------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "recording" not in st.session_state:
    st.session_state.recording = False

if "audio_data" not in st.session_state:
    st.session_state.audio_data = None

# ---------------------------
# UI
# ---------------------------
st.subheader("🎤 Talk to the Assistant")
col1, col2 = st.columns(2)

with col1:
    if st.button("🎙 Speak"):
        st.session_state.recording = True
        st.session_state.audio_data = None
        st.info("🎙 Recording... Speak now")

        st.session_state.audio_data = sd.rec(
            int(8 * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=1
        )

with col2:
    if st.button("⏹ Stop"):
        if st.session_state.recording:
            sd.stop()
            st.session_state.recording = False
            st.success("✅ Recording stopped")

# ---------------------------
# Process voice
# ---------------------------
if not st.session_state.recording and st.session_state.audio_data is not None:

    with st.spinner("🧠 Assistant is thinking..."):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav.write(tmp.name, SAMPLE_RATE, st.session_state.audio_data)

            with open(tmp.name, "rb") as f:
                files = {"audio": ("input.wav", f.read(), "audio/wav")}
                params = {}

                if st.session_state.session_id:
                    params["session_id"] = st.session_state.session_id

                try:
                    response = requests.post(
                        BACKEND_URL,
                        files=files,
                        params=params,
                        timeout=120
                    )
                except requests.exceptions.ReadTimeout:
                    st.error("⏳ Assistant took too long. Please try again.")
                    os.remove(tmp.name)
                    st.stop()

        os.remove(tmp.name)

    if response.status_code == 200:
        st.session_state.session_id = response.headers.get("X-Session-ID")

        st.success("🗣 Assistant is speaking...")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as out:
            out.write(response.content)
            out_path = out.name

        st.audio(out_path, format="audio/wav", autoplay=True)

    else:
        st.error("❌ Assistant failed to respond")
