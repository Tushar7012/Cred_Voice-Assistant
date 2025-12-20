# Voice Assistant – Architecture Document

## 1. System Overview

This project implements a **voice-first, multilingual, agentic AI system** that helps Indian citizens
identify and understand government welfare schemes.

The system operates end-to-end in native Indian languages and goes beyond a simple chatbot by
using explicit planning, tool execution, evaluation, and persistent memory.

---

## 2. High-Level Architecture

User (Voice)
↓
Streamlit Frontend
↓
FastAPI Backend (/voice)
↓
Speech-to-Text (Whisper)
↓
Agent Loop
├── Planner (LLM)
├── Executor (Tools)
└── Evaluator
↓
Conversation Memory (PostgreSQL)
↓
Text-to-Speech
↓
User (Audio Response)

---

## 3. Agent Lifecycle (Planner → Executor → Evaluator)

The system follows a **true agentic workflow**.

### Step 1: Planner
- Uses a local LLaMA model (Ollama)
- Interprets user intent
- Decides which action to take
- Extracts structured facts (age, income, state)
- Produces a **strict JSON plan**

### Step 2: Executor
- Executes the planner’s decision
- Uses tools such as:
  - Scheme Retriever (RAG)
  - Eligibility Checker
  - Direct Answer

### Step 3: Evaluator
- Validates response quality
- Rejects empty or generic replies
- Prevents fallback loops

---

## 4. Decision Flow

User Query
↓
Planner decides tool
↓
Tool execution
↓
Evaluator checks quality
↓
If valid → respond
If invalid → clarification prompt


---

## 5. Memory Architecture

Each user session maintains:

- Facts (age, income, state)
- Conversation history
- Detected contradictions

Memory is stored in PostgreSQL and persists across turns.

Example:

```json
{
  "facts": {
    "income": 200000,
    "state": "Odisha"
  },
  "history": [
    {"role": "user", "text": "ମୋ ଆୟ ୨ ଲକ୍ଷ"},
    {"role": "assistant", "text": "ଆପଣ PMAY ପାଇଁ ପାତ୍ର..."}
  ]
}

6. Prompt Design Strategy

Planner prompts are designed to:

Enforce language constraints

Prevent hallucination

Force explicit tool selection

Output only machine-readable JSON

This ensures deterministic behavior and safe execution.

7. Failure Handling

The system handles:

STT confidence failures

LLM timeouts (retry)

Invalid JSON outputs

Tool execution failures

Safe fallbacks ensure the system always responds.

8. Why This Is Not a Chatbot

| Feature       | Chatbot | This System |
| ------------- | ------- | ----------- |
| Single prompt | ❌       | ✅           |
| Tool usage    | ❌       | ✅           |
| Memory        | ❌       | ✅           |
| Planning      | ❌       | ✅           |
| Evaluation    | ❌       | ✅           |


9. Conclusion

This architecture demonstrates a production-aligned agentic AI system
with voice-first interaction, multilingual support, and explainable decision-making.
