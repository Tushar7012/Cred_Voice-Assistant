"""
Main Streamlit Application for Voice-First AI Assistant.
Provides voice-based interaction for government scheme discovery.
"""

import os
import sys
import uuid
import base64
import tempfile
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from loguru import logger

# Configure logging
logger.add("logs/app.log", rotation="10 MB", level="INFO")

# Import application modules
from app.config import settings, validate_settings
from app.models import UserProfile, CategoryEnum, GenderEnum
from agents.orchestrator import AgentOrchestrator
from agents.executor import executor_agent
from tools.eligibility_engine import eligibility_engine
from tools.scheme_retriever import scheme_retriever
from voice.tts import text_to_speech

# Try to import audio recorder
try:
    from streamlit_webrtc import webrtc_streamer, WebRtcMode
    import av
    WEBRTC_AVAILABLE = True
except ImportError:
    WEBRTC_AVAILABLE = False
    logger.warning("streamlit-webrtc not available, using file upload")

# Try to import audio utilities
try:
    from voice.audio_utils import audio_to_bytes
    from voice.stt import transcribe_audio
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False


# Page configuration
st.set_page_config(
    page_title="सरकारी योजना सहायक | Government Scheme Assistant",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #FF9933;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #138808;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton > button {
        background-color: #FF9933;
        color: white;
        font-size: 1.1rem;
        padding: 0.5rem 2rem;
    }
    .scheme-card {
        background: linear-gradient(135deg, #fff3e0 0%, #fff8e1 100%);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid #ffd54f;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "orchestrator" not in st.session_state:
        st.session_state.orchestrator = AgentOrchestrator()
        # Register tools with executor
        executor_agent.register_tool("eligibility_engine", eligibility_engine.execute)
        executor_agent.register_tool("scheme_retriever", scheme_retriever.execute)
        
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        
    if "is_recording" not in st.session_state:
        st.session_state.is_recording = False
        
    if "user_profile" not in st.session_state:
        st.session_state.user_profile = {}


def render_header():
    """Render the application header."""
    st.markdown('<h1 class="main-header">🇮🇳 सरकारी योजना सहायक</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">आवाज़ से जानें अपनी पात्रता | Voice-Powered Scheme Discovery</p>', unsafe_allow_html=True)


def render_sidebar():
    """Render the sidebar with user profile inputs."""
    with st.sidebar:
        st.header("👤 आपकी जानकारी")
        st.caption("अपनी जानकारी भरें या बातचीत में बताएं")
        
        # User profile form
        with st.expander("प्रोफ़ाइल जानकारी", expanded=True):
            age = st.number_input("उम्र (Age)", min_value=0, max_value=120, value=0, key="age_input")
            if age > 0:
                st.session_state.user_profile["age"] = age
            
            income = st.number_input("वार्षिक आय (Annual Income ₹)", min_value=0, value=0, step=10000, key="income_input")
            if income > 0:
                st.session_state.user_profile["annual_income"] = income
            
            category = st.selectbox(
                "श्रेणी (Category)",
                options=["चुनें", "सामान्य (General)", "SC", "ST", "OBC", "EWS"],
                key="category_input"
            )
            category_map = {"सामान्य (General)": "general", "SC": "sc", "ST": "st", "OBC": "obc", "EWS": "ews"}
            if category != "चुनें":
                st.session_state.user_profile["category"] = category_map.get(category)
            
            gender = st.selectbox(
                "लिंग (Gender)",
                options=["चुनें", "पुरुष (Male)", "महिला (Female)", "अन्य (Other)"],
                key="gender_input"
            )
            gender_map = {"पुरुष (Male)": "male", "महिला (Female)": "female", "अन्य (Other)": "other"}
            if gender != "चुनें":
                st.session_state.user_profile["gender"] = gender_map.get(gender)
            
            state = st.text_input("राज्य (State)", key="state_input")
            if state:
                st.session_state.user_profile["state"] = state
            
            is_bpl = st.checkbox("BPL कार्ड है (Have BPL Card)", key="bpl_input")
            st.session_state.user_profile["is_bpl"] = is_bpl
        
        st.divider()
        
        # Update orchestrator with profile
        if st.button("प्रोफ़ाइल अपडेट करें", use_container_width=True):
            st.session_state.orchestrator.update_user_profile(st.session_state.user_profile)
            st.success("प्रोफ़ाइल अपडेट हो गई!")
        
        # Settings
        st.header("⚙️ सेटिंग्स")
        
        with st.expander("API सेटिंग्स"):
            st.text_input("Sarvam API Key", type="password", key="sarvam_key")
            st.text_input("Groq API Key", type="password", key="groq_key")
            st.caption("API keys सेट करने के लिए .env फ़ाइल का उपयोग करें")
        
        if st.button("🔄 बातचीत रीसेट करें", use_container_width=True):
            st.session_state.messages = []
            st.session_state.orchestrator.reset()
            st.rerun()


def render_chat_interface():
    """Render the main chat interface."""
    chat_container = st.container()
    
    with chat_container:
        # Display chat history using native Streamlit chat components
        for message in st.session_state.messages:
            if message["role"] == "user":
                with st.chat_message("user", avatar="🎤"):
                    st.markdown(f"**आप:** {message['content']}")
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(f"**सहायक:** {message['content']}")
                    
                    # Show audio player with autoplay using HTML5
                    if "audio" in message and message["audio"]:
                        audio_bytes = message["audio"]
                        audio_b64 = base64.b64encode(audio_bytes).decode()
                        audio_html = f'''
                            <audio controls autoplay>
                                <source src="data:audio/wav;base64,{audio_b64}" type="audio/wav">
                            </audio>
                        '''
                        st.markdown(audio_html, unsafe_allow_html=True)


def render_input_section():
    """Render the input section with voice and text options."""
    st.divider()
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Text input
        user_input = st.text_input(
            "अपना सवाल टाइप करें (या आवाज़ में बोलें)",
            placeholder="उदाहरण: मैं एक किसान हूं, कौन सी योजना मेरे लिए है?",
            key="text_input"
        )
    
    with col2:
        send_button = st.button("भेजें 📤", use_container_width=True)
    
    # Audio file upload (fallback for voice)
    with st.expander("🎤 आवाज़ अपलोड करें"):
        audio_file = st.file_uploader(
            "ऑडियो फ़ाइल अपलोड करें",
            type=["wav", "mp3", "m4a"],
            key="audio_upload"
        )
        
        if audio_file:
            st.audio(audio_file)
            
            if st.button("आवाज़ से टेक्स्ट करें"):
                with st.spinner("आवाज़ समझ रहे हैं..."):
                    process_audio_input(audio_file)
    
    # Process text input
    if send_button and user_input:
        process_text_input(user_input)


def process_text_input(user_input: str):
    """Process text input from user."""
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.spinner("सोच रहे हैं..."):
        try:
            # Process through orchestrator
            result = st.session_state.orchestrator.process_user_input(user_input)
            
            response_text = result.get("response", "कुछ समस्या हुई, कृपया फिर से प्रयास करें।")
            
            # Generate audio response
            audio_bytes = None
            if settings.sarvam_api_key:
                try:
                    audio_bytes = text_to_speech(response_text)
                except Exception as e:
                    logger.warning(f"TTS failed: {e}")
            
            # Add assistant message
            st.session_state.messages.append({
                "role": "assistant",
                "content": response_text,
                "audio": audio_bytes,
                "tools_used": result.get("tools_used", []),
                "confidence": result.get("confidence", 0)
            })
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"माफ़ कीजिए, कुछ तकनीकी समस्या हुई। कृपया फिर से प्रयास करें।"
            })
    
    st.rerun()


def process_audio_input(audio_file):
    """Process uploaded audio file."""
    try:
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_file.read())
            tmp_path = tmp.name
        
        # Transcribe
        if AUDIO_AVAILABLE and settings.sarvam_api_key:
            text, confidence = transcribe_audio(tmp_path)
            
            if text:
                st.success(f"पहचाना गया: {text}")
                process_text_input(text)
            else:
                st.error("आवाज़ नहीं समझ पाए। कृपया फिर से बोलें।")
        else:
            st.warning("STT उपलब्ध नहीं है। कृपया API key सेट करें।")
        
        # Cleanup
        os.unlink(tmp_path)
        
    except Exception as e:
        logger.error(f"Audio processing failed: {e}")
        st.error("ऑडियो प्रोसेसिंग में समस्या हुई।")


def render_quick_actions():
    """Render quick action buttons."""
    st.subheader("🚀 जल्दी शुरू करें")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🌾 किसान योजनाएं", use_container_width=True):
            process_text_input("मैं एक किसान हूं, मेरे लिए कौन सी सरकारी योजनाएं हैं?")
    
    with col2:
        if st.button("🏠 आवास योजना", use_container_width=True):
            process_text_input("मुझे पक्का मकान बनाना है, कोई सरकारी मदद मिल सकती है?")
    
    with col3:
        if st.button("🏥 स्वास्थ्य योजना", use_container_width=True):
            process_text_input("स्वास्थ्य बीमा के लिए कौन सी योजना है?")
    
    col4, col5, col6 = st.columns(3)
    
    with col4:
        if st.button("👩 महिला योजनाएं", use_container_width=True):
            process_text_input("महिलाओं के लिए कौन सी सरकारी योजनाएं हैं?")
    
    with col5:
        if st.button("👴 पेंशन योजना", use_container_width=True):
            process_text_input("वृद्धावस्था पेंशन कैसे मिलेगी?")
    
    with col6:
        if st.button("📚 छात्रवृत्ति", use_container_width=True):
            process_text_input("छात्रों के लिए कौन सी छात्रवृत्ति योजनाएं हैं?")


def render_footer():
    """Render the footer."""
    st.divider()
    st.caption("""
    🇮🇳 **सरकारी योजना सहायक** - सभी भारतीयों के लिए सरकारी योजनाओं की जानकारी
    
    यह एक AI-powered सहायक है। कृपया आधिकारिक स्रोतों से भी जानकारी की पुष्टि करें।
    """)


def main():
    """Main application entry point."""
    # Initialize
    initialize_session_state()
    
    # Render components
    render_header()
    render_sidebar()
    
    # Main content
    if not st.session_state.messages:
        render_quick_actions()
        st.markdown("---")
        st.markdown("""
        ### 🎯 इस सहायक से आप क्या कर सकते हैं:
        - 🔍 अपनी पात्रता के अनुसार सरकारी योजनाएं खोजें
        - 📋 आवेदन प्रक्रिया और आवश्यक दस्तावेजों की जानकारी पाएं
        - 🗣️ हिंदी में बातचीत करें
        - 🎤 आवाज़ में सवाल पूछें
        
        **शुरू करने के लिए** ऊपर दिए गए बटन दबाएं या अपना सवाल टाइप/बोलें!
        """)
    else:
        render_chat_interface()
    
    render_input_section()
    render_footer()


if __name__ == "__main__":
    main()
