# Architecture Document

## System Overview

Voice-first agentic AI system for Indian government scheme discovery, operating end-to-end in Hindi.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User Interface                               │
│                    (Streamlit Web Application)                       │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │
│   │   Voice     │    │    Text     │    │   Profile   │            │
│   │   Input     │    │   Input     │    │    Form     │            │
│   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘            │
└──────────┼──────────────────┼──────────────────┼────────────────────┘
           │                  │                  │
           ▼                  │                  │
┌─────────────────────┐       │                  │
│   Voice Pipeline    │       │                  │
│  ┌───────────────┐  │       │                  │
│  │  Sarvam STT   │  │       │                  │
│  │   (Hindi)     │──┼───────┘                  │
│  └───────────────┘  │                          │
│  ┌───────────────┐  │                          │
│  │  Sarvam TTS   │  │                          │
│  │   (Hindi)     │  │                          │
│  └───────────────┘  │                          │
└─────────────────────┘                          │
           │                                     │
           ▼                                     ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        Agent Orchestrator                             │
│   ┌──────────────────────────────────────────────────────────────┐   │
│   │                     State Machine                             │   │
│   │  LISTENING → PLANNING → EXECUTING → EVALUATING → RESPONDING  │   │
│   └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│   │   Planner    │  │   Executor   │  │  Evaluator   │              │
│   │    Agent     │─▶│    Agent     │─▶│    Agent     │              │
│   └──────────────┘  └──────────────┘  └──────────────┘              │
└──────────────────────────────────────────────────────────────────────┘
           │                  │
           ▼                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          Tools Layer                                 │
│   ┌─────────────────────────┐    ┌─────────────────────────┐       │
│   │   Eligibility Engine    │    │   Scheme Retriever      │       │
│   │   (Rule-based)          │    │   (Vector Search)       │       │
│   └─────────────────────────┘    └─────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
           │                              │
           ▼                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          Data Layer                                  │
│   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│   │  Schemes JSON    │  │   ChromaDB       │  │  User Profiles   │ │
│   │  (Hindi)         │  │   (Vectors)      │  │  (Persistent)    │ │
│   └──────────────────┘  └──────────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          LLM Layer                                   │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │        Groq API (Llama 3.3 70B - Hindi Support)              │   │
│   │   • Planning prompts    • Execution logic                    │   │
│   │   • Evaluation          • Response generation                │   │
│   └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Agent Lifecycle

```
                    ┌─────────────┐
                    │   START     │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
            ┌──────▶│  LISTENING  │◀───────────────────┐
            │       └──────┬──────┘                    │
            │              │ Voice/Text Input          │
            │              ▼                           │
            │       ┌─────────────┐                    │
            │       │  PLANNING   │                    │
            │       │  • Parse intent                  │
            │       │  • Extract info                  │
            │       │  • Create plan                   │
            │       └──────┬──────┘                    │
            │              │                           │
            │              ▼                           │
            │       ┌─────────────┐                    │
            │       │  EXECUTING  │                    │
            │       │  • Run tools                     │
            │       │  • Collect results               │
            │       └──────┬──────┘                    │
            │              │                           │
            │              ▼                           │
            │       ┌─────────────┐                    │
            │       │ EVALUATING  │──── Need More ────▶│
            │       │  • Check completeness            │
            │       │  • Detect contradictions        │
            │       └──────┬──────┘                    │
            │              │ Complete                  │
            │              ▼                           │
            │       ┌─────────────┐                    │
            │       │ RESPONDING  │                    │
            │       │  • Generate response             │
            │       │  • TTS output                    │
            │       └──────┬──────┘                    │
            │              │                           │
            └──────────────┴───────────────────────────┘
```

---

## Memory Architecture

### Short-term Memory (Conversation)
- Last 10 conversation turns
- Current session context
- Extracted user information per turn

### Long-term Memory (User Context)
- Persistent user profiles (JSON files)
- Scheme interaction history
- Applied schemes tracking

### Contradiction Handling
```
User Input → Extract Info → Compare with Previous → 
    ├─ Match: Update profile
    └─ Mismatch: 
        ├─ Severity HIGH: Ask clarification
        └─ Severity LOW: Accept new value
```

---

## Tool Integration

### Tool 1: Eligibility Engine
```python
Input: {
    "user_profile": {
        "age": 45,
        "annual_income": 200000,
        "category": "obc",
        "state": "Maharashtra"
    }
}

Process:
1. Load all schemes
2. For each scheme:
   - Match age criteria
   - Match income criteria
   - Match category criteria
   - Match state criteria
   - Calculate match score

Output: {
    "schemes": [...],
    "match_scores": [...],
    "missing_info": [...]
}
```

### Tool 2: Scheme Retriever
```python
Input: {
    "query": "किसान के लिए योजना"
}

Process:
1. Embed query using multilingual model
2. Search ChromaDB for similar schemes
3. Return top-k matches

Output: {
    "schemes": [...],
    "relevance_scores": [...]
}
```

---

## Hindi Prompt Engineering

All prompts are in Hindi for native language processing:

**Planner Prompt Structure:**
```
System: आप एक योजना बनाने वाले एजेंट हैं...
User: उपयोगकर्ता प्रोफ़ाइल + बातचीत इतिहास + वर्तमान इनपुट
Output: JSON with plan steps
```

**Response Generation:**
```
- Use simple Hindi (avoid complex Sanskrit terms)
- Include specific rupee amounts
- Provide step-by-step application process
- List required documents in Hindi
```

---

## Error Handling

| Error Type | Detection | Recovery |
|------------|-----------|----------|
| STT Failure | API error or low confidence | Ask to repeat |
| LLM Timeout | 30s timeout | Retry with backoff |
| Tool Failure | Exception caught | Skip tool, continue |
| Missing Info | Profile incomplete | Ask clarification |
| Contradiction | Value mismatch | Request confirmation |

---

## Free Resources Used

| Component | Service | Free Tier |
|-----------|---------|-----------|
| STT | Sarvam AI | ₹1000 credits |
| TTS | Sarvam AI | ₹1000 credits |
| LLM | Groq API | Rate-limited free |
| Vector DB | ChromaDB | Open-source |
| Embeddings | sentence-transformers | Open-source |
| Frontend | Streamlit | Open-source |
