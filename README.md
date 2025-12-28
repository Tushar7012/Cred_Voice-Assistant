# 🇮🇳 Voice-First Government Scheme Assistant

A production-grade, voice-first agentic AI system that helps Indian citizens discover and apply for government welfare schemes. The system operates end-to-end in **Hindi** with true agentic workflow.

## Features

- **🎤 Voice-First Interaction**: Speak in Hindi, get responses in Hindi
- **🤖 Agentic Workflow**: Planner-Executor-Evaluator loop with explicit state machine
- **🔍 Smart Scheme Matching**: Rule-based eligibility engine + vector search
- **💾 Conversation Memory**: Multi-turn context with contradiction handling
- **🛠️ Two Integrated Tools**: Eligibility matching + semantic retrieval
- **🔄 Failure Handling**: Graceful recovery from errors

## Architecture

```
User (Voice/Text) → STT (Sarvam) → Agent Orchestrator → Tools → LLM (Groq) → TTS (Sarvam) → Response
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed diagrams.

## Quick Start

### 1. Prerequisites

- Python 3.9+
- Free API keys:
  - [Sarvam AI](https://www.sarvam.ai) - ₹1000 free credits for STT/TTS
  - [Groq](https://console.groq.com) - Free tier for LLM

### 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd Native_Voice_Assistant

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your API keys
SARVAM_API_KEY=your_sarvam_api_key
GROQ_API_KEY=your_groq_api_key
```

### 4. Run the Application

```bash
streamlit run app/main.py
```

Open http://localhost:8501 in your browser.

## Usage

### Voice Input
1. Click the audio upload section
2. Upload a Hindi audio file (WAV/MP3)
3. Click "आवाज़ से टेक्स्ट करें"

### Text Input
1. Type your question in Hindi
2. Click "भेजें"

### Example Queries

| Hindi | English Translation |
|-------|---------------------|
| मैं एक किसान हूं, मेरे लिए कौन सी योजना है? | I'm a farmer, which schemes are for me? |
| मेरी उम्र 35 साल है और आय 2 लाख है | My age is 35 and income is 2 lakh |
| मुझे पक्का मकान बनाना है | I want to build a pucca house |
| महिलाओं के लिए कौन सी योजनाएं हैं? | What schemes are for women? |

## Project Structure

```
Native_Voice_Assistant/
├── app/
│   ├── main.py           # Streamlit application
│   ├── config.py         # Configuration management
│   └── models.py         # Pydantic data models
├── voice/
│   ├── stt.py            # Sarvam STT integration
│   ├── tts.py            # Sarvam TTS integration
│   └── audio_utils.py    # Audio recording/playback
├── agents/
│   ├── planner.py        # Planner agent
│   ├── executor.py       # Executor agent
│   ├── evaluator.py      # Evaluator agent
│   └── orchestrator.py   # State machine
├── tools/
│   ├── eligibility_engine.py  # Rule-based matching
│   └── scheme_retriever.py    # Vector search
├── memory/
│   ├── conversation.py   # Short-term memory
│   ├── user_context.py   # Long-term memory
│   └── contradiction.py  # Contradiction handling
├── llm/
│   ├── groq_client.py    # Groq API wrapper
│   └── prompts.py        # Hindi prompts
├── data/
│   └── schemes/          # Government schemes data
├── docs/
│   └── ARCHITECTURE.md   # Architecture documentation
├── transcripts/          # Evaluation transcripts
└── tests/                # Unit tests
```

## Agentic Workflow

### State Machine

```
LISTENING → PLANNING → EXECUTING → EVALUATING → RESPONDING
     ↑                                    │
     └────────────────────────────────────┘
```

### Agent Responsibilities

| Agent | Responsibility |
|-------|----------------|
| **Planner** | Parse intent, identify missing info, create action plan |
| **Executor** | Run tools, collect results, handle failures |
| **Evaluator** | Validate completeness, detect contradictions |

## Tools

### 1. Eligibility Engine
- Rule-based matching against scheme criteria
- Checks: age, income, category, state, gender, BPL status
- Returns match score and missing criteria

### 2. Scheme Retriever
- ChromaDB vector database
- Multilingual embeddings (Hindi support)
- Semantic search for relevant schemes

## Memory Features

- **Conversation Memory**: Last 10 turns with context
- **User Profile**: Persists across sessions
- **Contradiction Detection**: Handles conflicting information
- **Info Extraction**: Automatically extracts user details from conversation

## API Keys Setup

### Sarvam AI (STT/TTS)
1. Go to https://www.sarvam.ai
2. Sign up for free account
3. Get ₹1000 free credits
4. Copy API key to `.env`

### Groq (LLM)
1. Go to https://console.groq.com
2. Create free account
3. Generate API key
4. Copy to `.env`

## Supported Schemes

Current database includes:
- PM-KISAN (किसान सम्मान निधि)
- PM Awas Yojana (आवास योजना)
- Ayushman Bharat (आयुष्मान भारत)
- PM Ujjwala (उज्ज्वला योजना)
- Sukanya Samriddhi (सुकन्या समृद्धि)
- PM Shram Yogi Maan-dhan (श्रम योगी मान-धन)
- Jan Dhan Yojana (जन धन योजना)
- Mudra Yojana (मुद्रा योजना)
- And more...

## Testing

```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest tests/ --cov=app --cov=agents --cov=tools
```

## Evaluation Transcripts

See the `transcripts/` folder for:
- **success_cases.md**: Complete user journeys
- **failure_cases.md**: Error recovery examples
- **edge_cases.md**: Contradiction handling, multi-turn conversations

## Technology Stack

| Component | Technology | License |
|-----------|------------|---------|
| STT | Sarvam AI | Freemium |
| TTS | Sarvam AI | Freemium |
| LLM | Groq (Llama 3.3) | Freemium |
| Vector DB | ChromaDB | Apache 2.0 |
| Embeddings | sentence-transformers | Apache 2.0 |
| Frontend | Streamlit | Apache 2.0 |
| Language | Python 3.9+ | PSF |

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- [Sarvam AI](https://www.sarvam.ai) for Indian language STT/TTS
- [Groq](https://groq.com) for fast LLM inference
- [AI4Bharat](https://ai4bharat.org) for Indian language NLP research
- [myScheme Portal](https://www.myscheme.gov.in) for scheme information
