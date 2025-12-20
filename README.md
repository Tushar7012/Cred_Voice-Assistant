## 🎙️ Voice Assistant – Agentic AI System

A voice-first, multilingual, agentic AI system that helps Indian citizens understand and discover government welfare schemes using planning, tool execution, evaluation, and persistent memory — not a simple chatbot.

## Project Overview

This project implements a production-aligned AI agent that:

- Accepts voice input in Indian languages

- Understands user intent using an LLM planner

- Retrieves verified scheme information using RAG

- Checks eligibility using structured rules

- Maintains conversation memory across turns

- Responds back using Text-to-Speech

- The system follows a Planner → Executor → Evaluator lifecycle and avoids hallucinations by design.

## ✨ Key Features

- Voice-First Interaction (No typing required)

- Multilingual Support (Hindi, Odia, Marathi, etc.)

- True Agentic Workflow

- Explicit Tool Usage

- Persistent Memory (PostgreSQL)

- RAG-based Scheme Retrieval

- Eligibility Checking

- Safe Fallbacks & Error Handling

## 🧠 Why This Is NOT a Chatbot

| Feature       | Traditional Chatbot | This System |
| ------------- | ------------------- | ----------- |
| Single prompt | ❌                   | ✅           |
| Tool usage    | ❌                   | ✅           |
| Planning      | ❌                   | ✅           |
| Evaluation    | ❌                   | ✅           |
| Memory        | ❌                   | ✅           |

## 🏗️ High-Level Architecture

User (Voice)
   ↓
Streamlit Frontend
   ↓
FastAPI Backend (/voice)
   ↓
Speech-to-Text (Whisper)
   ↓
Agent Loop
   ├── Planner (LLM via Ollama)
   ├── Executor (Tools / RAG / Rules)
   └── Evaluator (Response Validation)
   ↓
Conversation Memory (PostgreSQL)
   ↓
Text-to-Speech
   ↓
User (Audio Response)


## 🔁 Agent Lifecycle
# 1️⃣ Planner (LLM)

- Extracts structured facts (age, income, state)

- Decides which tool to use

- Outputs strict JSON plan

# 2️⃣ Executor

- Executes selected tool:

- Scheme Retriever (RAG)

- Eligibility Checker

- Direct Answer

# 3️⃣ Evaluator

- Validates response quality

- Prevents fallback loops

- Rejects empty or generic replies

## 🧠 Memory Architecture

- Each user session maintains:

- Facts (age, income, state)

- Conversation history

- Detected contradictions

- Memory persists across turns using PostgreSQL.

Example:
```json
{
  "facts": {
    "income": 200000,
    "state": "Odisha"
  },
  "history": [
    { "role": "user", "text": "ମୋ ଆୟ ୨ ଲକ୍ଷ" },
    { "role": "assistant", "text": "ଆପଣ PMAY ପାଇଁ ଯୋଗ୍ୟ..." }
  ]
}

```

## Prompt Design Strategy

- Planner prompts are designed to:

- Enforce language constraints

- Prevent hallucinations

- Force explicit tool selection

- Output JSON-only responses

- Enable deterministic execution

## Failure Handling

- The system safely handles:

- STT confidence failures

- LLM timeouts (retry mechanism)

- Invalid JSON outputs

- Tool execution failures

## Project Structure

backend/
├── app/
│   ├── agent/          # Planner, Executor, Evaluator
│   ├── api/            # FastAPI endpoints
│   ├── rag/            # FAISS + Retriever
│   ├── tools/          # Scheme & Eligibility tools
│   ├── memory/         # Session memory store
│   ├── stt/            # Speech-to-Text
│   ├── tts/            # Text-to-Speech
│   ├── utils/          # Helpers & contradiction detection
│   └── main.py
├── streamlit_app.py    # Voice UI
└── ARCHITECTURE.md

## How to Run

# Start Ollama
1. Install Ollama: https://ollama.com/download
2. ollama run llama3:8b-instruct-q4_0

# Start Backend
uvicorn app.main:app --reload

# Start Backend
uvicorn app.main:app --reload

## Example Voice Queries

Hindi:
“प्रधानमंत्री आवास योजना के बारे में बताइए।”

Odia:
“ମୋ ଆୟ ୨ ଲକ୍ଷ ଟଙ୍କା, ମୁଁ କେଉଁ ଯୋଜନା ପାଇଁ ଯୋଗ୍ୟ?”

Marathi:
“माझे उत्पन्न दोन लाख आहे.”

## ✅ Conclusion

This project demonstrates a real-world, agentic AI system with:

- Voice-first interaction

- Multilingual understanding

- Tool-based reasoning

- Persistent memory

- Safe, explainable decisions